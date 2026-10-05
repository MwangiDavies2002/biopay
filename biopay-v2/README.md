# BioPay v2 — Biometric / Passwordless Payment Prototype

BioPay v2 is a local proof-of-concept for a passwordless payment authorization network. It separates the **financial core** from the **biometric/risk layer** and keeps raw biometric data out of the payment database.

## Stack

- **Java 21 + Spring Boot** — wallets, payment requests, authorization, ledger, merchant APIs
- **Python + FastAPI** — biometric/liveness adapter and fraud/risk scoring
- **Next.js** — merchant and customer demo applications
- **MySQL 8** — transactional data and double-entry ledger
- **Redis 7** — short-lived payment challenges/nonces and replay protection
- **Docker Compose** — local development environment

## Important prototype limitation

The included UI uses a **development-only simulated passkey authorization** so the full flow can be tested without fingerprint hardware. It is deliberately disabled when `BIOPAY_DEMO_MODE=false`.

The production path is documented in `docs/SECURITY.md`: use WebAuthn/passkeys for remote authentication and a certified reader/SDK for dedicated POS fingerprint capture. Do **not** store raw fingerprint images or ordinary hashes of fingerprint scans.

## Run

Requirements: Docker Desktop / Docker Engine with Compose.

```bash
docker compose up --build
```

Then open:

- Merchant app: http://localhost:3000
- Customer app: http://localhost:3001
- Payment API: http://localhost:8080
- Biometric/risk API docs: http://localhost:8000/docs

The Java API root displays links to the apps and its health endpoint. The local
Compose override publishes Redis on port 6380 to avoid an existing service on 6379;
containers continue to communicate with Redis on its internal port 6379.

Run the repeatable simulation after starting the services:

```powershell
python scripts/simulate.py --count 5000 --workers 16
```

For a larger run that preserves the earlier report:

```powershell
python scripts/simulate.py --count 100000 --workers 32 --progress-every 1000 --report artifacts/simulation-report-100000.json
```

It seeds separate simulation identities and runs successful payments, simultaneous
replays, liveness/device failures, insufficient funds, and invalid input cases. It
also verifies expiry, risk decisions, balanced ledger entries and wallet totals.
Results are saved to `artifacts/simulation-report.json`. Simulation rows are retained
for inspection; the seeded demo wallets are not modified by this script.

The merchant and customer dashboards include wallet balances, payment cards, expiry
countdowns and direct payment links. Merchant requests update automatically when a
customer approves them. The API landing page and interactive risk explorer share
the same responsive design.

Optional UI verification on Windows with Chrome installed:

```powershell
python -m pip install --target .tools/preview -r scripts/requirements-ui.txt
python scripts/verify-ui.py
```

This checks all four pages at desktop, tablet and phone widths, then exercises the
checkout UI with mocked payments. It saves screenshots and the result report under
`artifacts/ui` and does not debit the demo wallets.

The MySQL schema is created automatically by Flyway when the payment service starts.

## Demo flow

1. Open the merchant app and create a KES payment request.
2. Copy the returned payment ID.
3. Open the customer app and authorize that payment ID.
4. The Java service validates the Redis nonce, calls the Python risk engine, locks the payer wallet, posts balanced debit/credit ledger entries, and marks the request approved.
5. Refresh balances in the merchant/customer apps.

Seeded demo identities:

- Customer `USER-DEMO-001`, initial balance KES 100,000
- Merchant `MERCHANT-DEMO-001`, initial balance KES 0

## Project layout

```text
biopay-v2/
├── services/
│   ├── payment-core/        # Spring Boot financial core
│   └── biometric-risk/      # FastAPI biometric/risk service
├── frontend/
│   ├── merchant-web/        # Next.js merchant demo
│   └── customer-web/        # Next.js customer demo
├── infrastructure/
│   └── mysql/               # local DB configuration notes
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SECURITY.md
│   └── API.md
└── docker-compose.yml
```

## What to implement next

1. Replace simulated authorization with WebAuthn/passkeys.
2. Add device registration and public-key credential storage.
3. Add signed transaction payloads (`payment_id`, amount, merchant, nonce, expiry).
4. Add dedicated fingerprint-reader adapter with liveness detection.
5. Add proper KYC/onboarding boundaries and audited admin controls.
6. Add sandbox payment-rail connectors only after the ledger and authorization model pass security tests.

This is a software prototype, not a production banking system. Real-money deployment requires security reviews, compliance work, operational controls, key management/HSM design, reconciliation, dispute handling, monitoring, and integration approval from regulated payment partners.

### Optional command-line demo

After `docker compose up --build`, on Windows PowerShell run:

```powershell
./scripts/demo.ps1
```

or on Bash:

```bash
./scripts/demo.sh
```
