"""Check recovery after a local risk API outage; always restore the service."""
import json
import subprocess
import time
import urllib.request
import urllib.error
from simulate import ROOT, API, PREFIX, seed, call, expect, invariants


def compose(*args):
    subprocess.run(['docker', 'compose', *args], cwd=ROOT, check=True)


def main():
    seed(1)
    body = dict(payerUserId=PREFIX+'-U0', merchantId=PREFIX+'-M', amount=0.01, currency='KES')
    auth = dict(deviceId=PREFIX+'-D0', liveness=True)
    p = expect(call('/payment-requests', body), 200)
    path = '/payment-requests/'+p['id']+'/demo-authorize'
    expect(call(path, auth | {'liveness': False}), 400, 'liveness')
    expect(call(path, auth | {'deviceId': 'UNKNOWN'}), 400, 'not registered')
    expect(call(path, auth), 200, 'APPROVED')
    p = expect(call('/payment-requests', body), 200)
    path = '/payment-requests/'+p['id']+'/demo-authorize'
    before = expect(call('/wallets/'+PREFIX+'-U0'), 200)['balance']
    try:
        compose('stop', 'biometric-risk')
        expect(call(path, auth), 503, 'Risk service is unavailable')
        expect(call('/payment-requests/'+p['id']), 200, 'PENDING')
        assert expect(call('/wallets/'+PREFIX+'-U0'), 200)['balance'] == before
    finally:
        compose('start', 'biometric-risk')
        for _ in range(30):
            try:
                expect(call('/health', base='http://localhost:8000'), 200, 'ok')
                break
            except Exception:
                time.sleep(1)
        else:
            raise AssertionError('Risk service did not recover')
    expect(call(path, auth), 200, 'APPROVED')
    # Rejected inputs should expose an error message, rather than Spring's generic page.
    r = urllib.request.Request(API+'/payment-requests', data=b'{broken', headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(r)
        raise AssertionError('Malformed JSON was accepted')
    except urllib.error.HTTPError as error:
        assert error.code == 400
        assert 'error' in json.loads(error.read())
    for origin in ['http://localhost:3000', 'http://localhost:3001']:
        r = urllib.request.Request(API+'/payment-requests', method='OPTIONS',
                headers={'Origin': origin, 'Access-Control-Request-Method': 'POST',
                         'Access-Control-Request-Headers': 'content-type'})
        with urllib.request.urlopen(r) as response:
            assert response.headers['Access-Control-Allow-Origin'] == origin
    report = dict(passed=True, checks=['retry after failed liveness', 'retry after invalid device',
                  'risk outage returns 503', 'risk outage preserves balance and pending payment',
                  'successful retry after risk recovery', 'malformed JSON returns readable 400',
                  'CORS accepts both demo apps'], invariants=invariants(2, 1))
    out = ROOT/'artifacts'/'recovery-report.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
