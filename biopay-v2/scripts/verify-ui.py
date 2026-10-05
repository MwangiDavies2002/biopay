"""Desktop/mobile UI verification in a separate headless Chrome, using mock payments."""
import json
from pathlib import Path
import sys
import time
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.tools/preview'))
from playwright.sync_api import sync_playwright

OUTPUT = ROOT / 'artifacts/ui'
OUTPUT.mkdir(parents=True, exist_ok=True)
PAGES = [('merchant', 'http://localhost:3000'), ('customer', 'http://localhost:3001'),
         ('api', 'http://localhost:8080'), ('risk', 'http://localhost:8000/docs')]
PAYMENT_ID = 'PAY-00000000-0000-4000-8000-000000000001'


def verify_layout(page, name, width):
    overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
    assert not overflow, f'{name} has horizontal overflow at {width}px'
    assert page.locator('h1').count() == 1, f'{name} needs one page heading'
    assert page.locator('nav[aria-label="Workspace navigation"]').count() == 1
    page.screenshot(path=str(OUTPUT / f'{name}-{width}.png'), full_page=True)


def main():
    report = {'pages': [], 'interaction_checks': [], 'errors': []}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                                   headless=True, args=['--host-resolver-rules=MAP localhost [::1]'])
        context = browser.new_context(viewport={'width': 1440, 'height': 1050}, reduced_motion='reduce')
        context.on('weberror', lambda error: report['errors'].append(str(error.error)))
        for name, url in PAGES:
            page = context.new_page()
            response = page.goto(url, wait_until='networkidle', timeout=45000)
            assert response.status == 200, f'{name} returned {response.status}'
            if name in ['merchant', 'customer']:
                page.get_by_text('Balance up to date', exact=True).wait_for()
            if name == 'api':
                page.get_by_text('Payment service online', exact=True).wait_for()
            if name == 'risk':
                page.locator('.swagger-ui .opblock').first.wait_for()
            for width in [1440, 1024, 768, 390, 320]:
                page.set_viewport_size({'width': width, 'height': 1050 if width==1440 else 844})
                verify_layout(page, name, width)
            report['pages'].append({'name': name, 'desktop_mobile': 'passed', 'status': response.status})
            page.close()

        # Exercise payment UI without moving funds in the demo wallets.
        payment = dict(id=PAYMENT_ID, payerUserId='USER-DEMO-001', merchantId='MERCHANT-DEMO-001',
                       amount=12500, currency='KES', status='PENDING', challenge='ui-test',
                       expiresAt=(datetime.now(timezone.utc)+timedelta(seconds=90)).isoformat())
        def payments(route):
            result = dict(payment)
            if route.request.url.endswith('/demo-authorize'):
                result['status'] = 'APPROVED'
            route.fulfill(status=200, content_type='application/json', body=json.dumps(result))
        context.route('**/api/v1/payment-requests', payments)
        context.route('**/api/v1/payment-requests/**', payments)
        merchant = context.new_page()
        merchant.goto(PAGES[0][1], wait_until='networkidle')
        merchant.get_by_label('Payment amount', exact=True).fill('0')
        merchant.get_by_role('button', name='Create payment request').click()
        merchant.get_by_role('alert').filter(has_text='at least KES 0.01').wait_for()
        merchant.get_by_label('Payment amount', exact=True).fill('12500')
        merchant.get_by_role('button', name='Create payment request').click()
        merchant.get_by_role('heading', name='Your payment request', exact=True).wait_for()
        handoff = merchant.get_by_role('link', name='Open in customer app').get_attribute('href')
        assert PAYMENT_ID in handoff
        report['interaction_checks'] += ['merchant amount validation', 'readable payment result', 'customer handoff link']
        customer = context.new_page()
        customer.goto(handoff, wait_until='networkidle')
        customer.get_by_text('Awaiting approval', exact=True).wait_for()
        customer.get_by_role('button', name='Approve KES 12,500.00 · Demo', exact=True).click()
        customer.get_by_role('status').filter(has_text="You're all set").wait_for()
        customer.get_by_text('Approved', exact=True).wait_for()
        assert customer.get_by_role('button', name='Approve KES').count() == 0
        report['interaction_checks'] += ['auto-load linked payment', 'approval confirmation', 'approved payment cannot be resubmitted']
        customer.get_by_label('Payment ID', exact=True).fill('bad-id')
        customer.get_by_role('button', name='Find payment', exact=True).click()
        customer.get_by_role('alert').filter(has_text='valid payment ID').wait_for()
        report['interaction_checks'].append('invalid payment ID error')

        payment['expiresAt']=(datetime.now(timezone.utc)-timedelta(seconds=5)).isoformat()
        expired=context.new_page()
        expired.goto(handoff,wait_until='networkidle')
        expired.get_by_text('Expired',exact=True).wait_for()
        assert expired.get_by_role('button',name='Approve KES').count()==0
        report['interaction_checks'].append('expired requests cannot be approved')
        payment['payerUserId']='OTHER-CUSTOMER'
        wrong_customer=context.new_page()
        wrong_customer.goto(handoff,wait_until='networkidle')
        wrong_customer.get_by_role('alert').filter(has_text='different customer').wait_for()
        report['interaction_checks'].append('different customer payment rejected by UI')

        offline = context.new_page()
        offline.route('**/api/v1/wallets/**', lambda route: route.abort())
        offline.goto(PAGES[0][1], wait_until='networkidle')
        offline.get_by_role('alert').filter(has_text='Cannot reach the payment API').wait_for()
        report['interaction_checks'].append('unavailable wallet error')
        risk=context.new_page()
        risk.goto(PAGES[3][1],wait_until='networkidle')
        risk.locator('.opblock-post .opblock-summary').click()
        risk.get_by_role('button',name='Try it out',exact=True).click()
        risk.locator('textarea').fill(json.dumps(dict(paymentId='UI-PREVIEW',payerUserId='USER-DEMO-001',
                merchantId='MERCHANT-DEMO-001',deviceId='DEVICE-DEMO-001',amount=1,currency='KES',
                liveness=True,recentAttemptCount=0)))
        with risk.expect_response('**/v1/risk/score') as scored:
            risk.get_by_role('button',name='Execute',exact=True).click()
        assert scored.value.status==200 and scored.value.json()['decision']=='APPROVE'
        risk.set_viewport_size({'width':390,'height':844})
        assert not risk.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
        risk.screenshot(path=str(OUTPUT/'risk-interactive-390.png'),full_page=True)
        report['interaction_checks'].append('Swagger interactive risk request returns APPROVE')
        assert not report['errors'], report['errors']
        browser.close()
    (OUTPUT / 'verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
