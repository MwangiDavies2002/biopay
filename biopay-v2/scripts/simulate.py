"""Run configurable real HTTP payment scenarios against the local Docker stack.

Uses separate seeded simulation identities and preserves existing demo balances.
Run from any directory: python scripts/simulate.py --count 5000 --workers 16
"""
import argparse
import concurrent.futures
import datetime
import decimal
import json
import pathlib
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
API = 'http://localhost:8080/api/v1'
PREFIX = 'SIM-' + uuid.uuid4().hex[:12]
KINDS = ['approved', 'replay', 'concurrent_replay', 'liveness_rejected',
         'device_rejected', 'insufficient_funds', 'unknown_payer',
         'excess_precision', 'unsupported_currency', 'invalid_amount']
HTTP_STATS = Counter()
HTTP_LOCK = threading.Lock()


def sql(statement):
    result = subprocess.run(
        ['docker', 'compose', 'exec', '-T', '-e', 'MYSQL_PWD=biopay_dev_password',
         'mysql', 'mysql', '-ubiopay', '-Dbiopay', '-N', '-B'],
        input=statement, text=True, capture_output=True, cwd=ROOT, check=True)
    return result.stdout.strip()


def call(path, body=None, base=API):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(base + path, data=data, headers={'Content-Type': 'application/json'})
    status = 'network_error'
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = str(response.status)
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        status = str(error.code)
        return error.code, json.loads(error.read())
    finally:
        with HTTP_LOCK:
            HTTP_STATS[status] += 1


def expect(result, status, contains=None):
    actual, body = result
    assert actual == status, f'Expected HTTP {status}, got {actual}: {body}'
    if contains:
        assert contains.lower() in str(body).lower(), f'Missing {contains!r}: {body}'
    return body


def seed(workers):
    statements = [f"INSERT INTO merchant(id,name,status) VALUES ('{PREFIX}-M','Simulation merchant','ACTIVE');",
                  f"INSERT INTO wallet(id,owner_type,owner_id,currency,balance) VALUES ('{PREFIX}-WM','MERCHANT','{PREFIX}-M','KES',0);"]
    for i in range(workers):
        user, device = f'{PREFIX}-U{i}', f'{PREFIX}-D{i}'
        statements += [f"INSERT INTO app_user(id,display_name,status) VALUES ('{user}','Simulation customer','ACTIVE');",
                       f"INSERT INTO wallet(id,owner_type,owner_id,currency,balance) VALUES ('{PREFIX}-W{i}','USER','{user}','KES',10000);",
                       f"INSERT INTO registered_device(id,user_id,status) VALUES ('{device}','{user}','ACTIVE');"]
    sql('\n'.join(statements))


def scenario(index, workers):
    kind = index % len(KINDS)
    actor = index % workers
    request = dict(payerUserId=f'{PREFIX}-U{actor}', merchantId=f'{PREFIX}-M', amount=0.01, currency='KES')
    auth = dict(deviceId=f'{PREFIX}-D{actor}', liveness=True)
    if kind >= 6:
        fields = {6: {'payerUserId': 'UNKNOWN'}, 7: {'amount': 0.01001},
                  8: {'currency': 'USD'}, 9: {'amount': [-1, 0, None][index % 3]}}
        expect(call('/payment-requests', request | fields[kind]), 400, 'error')
        return dict(kind=KINDS[kind], approved=0)
    if kind == 5:
        request['amount'] = 1000000
    payment = expect(call('/payment-requests', request), 200, 'PENDING')
    path = '/payment-requests/' + payment['id']
    if kind == 2:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: call(path + '/demo-authorize', auth), range(4)))
        assert Counter(status for status, _ in results) == {200: 1, 400: 3}, results
        for status, body in results:
            if status == 400:
                assert 'not pending' in body.get('error', '').lower(), body
    elif kind <= 1:
        expect(call(path + '/demo-authorize', auth), 200, 'APPROVED')
        if kind == 1:
            expect(call(path + '/demo-authorize', auth), 400, 'not pending')
    else:
        auth |= {3: {'liveness': False}, 4: {'deviceId': 'UNKNOWN'}, 5: {}}[kind]
        reason = {3: 'liveness', 4: 'not registered', 5: 'Insufficient funds'}[kind]
        expect(call(path + '/demo-authorize', auth), 400, reason)
    expect(call(path), 200, 'APPROVED' if kind <= 2 else 'PENDING')
    return dict(kind=KINDS[kind], approved=int(kind <= 2))


def extra_checks():
    expect(call('/payment-requests/UNKNOWN'), 404, 'not found')
    expect(call('/wallets/UNKNOWN'), 404, 'not found')
    request = dict(payerUserId=f'{PREFIX}-U0', merchantId=f'{PREFIX}-M', amount=0.01, currency='KES')
    payment = expect(call('/payment-requests', request), 200)
    sql(f"UPDATE payment_request SET expires_at=UTC_TIMESTAMP(6)-INTERVAL 1 SECOND WHERE id='{payment['id']}';")
    expect(call('/payment-requests/' + payment['id'] + '/demo-authorize',
                dict(deviceId=f'{PREFIX}-D0', liveness=True)), 400, 'expired')
    expect(call('/payment-requests/' + payment['id']), 200, 'EXPIRED')
    risk = dict(paymentId='SIM', payerUserId=f'{PREFIX}-U0', merchantId=f'{PREFIX}-M',
                deviceId=f'{PREFIX}-D0', amount=1, currency='KES', liveness=True, recentAttemptCount=0)
    for fields, decision in [({}, 'APPROVE'), ({'liveness': False}, 'DECLINE'),
                             ({'amount': 100000, 'recentAttemptCount': 5}, 'STEP_UP')]:
        expect(call('/v1/risk/score', risk | fields, 'http://localhost:8000'), 200, decision)
    for fields in [{'amount': -1}, {'currency': 'bad'}, {'recentAttemptCount': -1}]:
        expect(call('/v1/risk/score', risk | fields, 'http://localhost:8000'), 422)


def invariants(approved, workers):
    checks = {}
    checks['posted_transactions'] = int(sql(f"SELECT COUNT(*) FROM payment_transaction t JOIN payment_request p ON p.id=t.payment_request_id WHERE p.merchant_id='{PREFIX}-M';"))
    assert checks['posted_transactions'] == approved, checks
    checks['ledger_entries'] = int(sql(f"SELECT COUNT(*) FROM ledger_entry l JOIN payment_transaction t ON t.id=l.transaction_id JOIN payment_request p ON p.id=t.payment_request_id WHERE p.merchant_id='{PREFIX}-M';"))
    assert checks['ledger_entries'] == approved * 2, checks
    checks['unbalanced_transactions'] = int(sql(f"SELECT COUNT(*) FROM (SELECT l.transaction_id FROM ledger_entry l JOIN payment_transaction t ON t.id=l.transaction_id JOIN payment_request p ON p.id=t.payment_request_id WHERE p.merchant_id='{PREFIX}-M' GROUP BY l.transaction_id HAVING COUNT(*)<>2 OR SUM(CASE WHEN l.direction='DEBIT' THEN -l.amount ELSE l.amount END)<>0) bad;"))
    assert checks['unbalanced_transactions'] == 0, checks
    checks['wallet_ledger_mismatches'] = int(sql(f"SELECT COUNT(*) FROM wallet w LEFT JOIN (SELECT wallet_id,SUM(CASE WHEN direction='CREDIT' THEN amount ELSE -amount END) change_amount FROM ledger_entry GROUP BY wallet_id) l ON l.wallet_id=w.id WHERE w.owner_id LIKE '{PREFIX}-%' AND w.balance <> (CASE WHEN w.owner_type='USER' THEN 10000 ELSE 0 END) + COALESCE(l.change_amount,0);"))
    assert checks['wallet_ledger_mismatches'] == 0, checks
    checks['approved_payments'] = int(sql(f"SELECT COUNT(*) FROM payment_request WHERE merchant_id='{PREFIX}-M' AND status='APPROVED';"))
    assert checks['approved_payments'] == approved, checks
    total = decimal.Decimal(sql(f"SELECT SUM(balance) FROM wallet WHERE owner_id LIKE '{PREFIX}-%';"))
    assert total == workers * 10000, f'Balance conservation failed: {total}'
    merchant = decimal.Decimal(sql(f"SELECT balance FROM wallet WHERE owner_id='{PREFIX}-M';"))
    assert merchant == decimal.Decimal('0.01') * approved, f'Merchant balance mismatch: {merchant}'
    checks |= dict(total_wallet_balance=str(total), merchant_balance=str(merchant))
    return checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=5000)
    parser.add_argument('--workers', type=int, default=16)
    parser.add_argument('--report', default='artifacts/simulation-report.json')
    parser.add_argument('--progress-every', type=int, default=250)
    args = parser.parse_args()
    assert args.count > 0 and args.workers > 0 and args.progress_every > 0
    started = time.monotonic()
    demo_before = sql("SELECT owner_id,balance FROM wallet WHERE owner_id IN ('USER-DEMO-001','MERCHANT-DEMO-001') ORDER BY owner_id;")
    seed(args.workers)
    results, failures, counts = [], [], Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        indices = iter(range(args.count))
        futures = {}
        n = 0
        def submit_next():
            index = next(indices, None)
            if index is not None:
                futures[pool.submit(scenario, index, args.workers)] = index
        for _ in range(min(args.count, args.workers * 4)):
            submit_next()
        while futures:
            done, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                index = futures.pop(future)
                n += 1
                try:
                    result = future.result()
                    results.append(result)
                    counts[result['kind']] += 1
                except Exception as error:
                    failures.append(dict(scenario=index, error=str(error)))
                    if len(failures) <= 10:
                        print(f'Scenario {index} failed: {error}', flush=True)
                if n % args.progress_every == 0 or n == args.count:
                    elapsed = time.monotonic() - started
                    print(f'{n}/{args.count} completed; failures={len(failures)}; elapsed={elapsed:.1f}s; scenarios/s={n/elapsed:.1f}', flush=True)
                submit_next()
    checks = {}
    try:
        extra_checks()
        checks = invariants(sum(r['approved'] for r in results), args.workers)
        assert demo_before == sql("SELECT owner_id,balance FROM wallet WHERE owner_id IN ('USER-DEMO-001','MERCHANT-DEMO-001') ORDER BY owner_id;"), 'Demo balances were changed'
        checks['demo_balances_unchanged'] = True
    except Exception as error:
        failures.append(dict(scenario='extra checks / ledger invariants', error=str(error)))
    report = dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  simulation_prefix=PREFIX, requested=args.count, passed=len(results),
                  failures=failures, scenarios=dict(counts), invariants=checks,
                  elapsed_seconds=round(time.monotonic()-started, 2), workers=args.workers,
                  http_requests=sum(HTTP_STATS.values()), http_status_counts=dict(HTTP_STATS))
    out = ROOT / args.report
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)
    raise SystemExit(bool(failures))


if __name__ == '__main__':
    main()
