# Prototype API

Base URL: `http://localhost:8080/api/v1`

`GET http://localhost:8080/` serves the API landing page with links to the local apps.

Errors return a JSON `error` message. Invalid inputs, unavailable wallets/currencies,
failed liveness/device checks, insufficient funds and replays return HTTP 400.
Unknown payment/wallet lookups return 404. An unavailable risk service returns 503;
the payment stays pending and can be retried after recovery.

## Health

`GET /health`

## Wallet

`GET /wallets/{ownerId}`

## Create payment request

`POST /payment-requests`

```json
{
  "payerUserId": "USER-DEMO-001",
  "merchantId": "MERCHANT-DEMO-001",
  "amount": 12500,
  "currency": "KES"
}
```

Returns a payment request containing a short-lived nonce/challenge and expiry.

## Read payment request

`GET /payment-requests/{paymentId}`

## Development-only authorization

`POST /payment-requests/{paymentId}/demo-authorize`

```json
{
  "deviceId": "DEVICE-DEMO-001",
  "liveness": true
}
```

The payment core validates the challenge, calls the Python risk API, atomically posts the ledger entries, consumes the nonce, and marks the payment approved.

The device must be active and registered to the payer. Concurrent authorizations
lock the payment before checking its state, so only one can post. Currency uses
the schema's `CHAR(3)` mapping; amount precision is capped at four decimal places.

Run `python scripts/simulate.py --count 5000 --workers 16` to verify payment flows,
replay protection and ledger balances. `python scripts/check-recovery.py` additionally
checks authorization retries across a risk service outage and restores the service.

## Risk service

`POST http://localhost:8000/v1/risk/score`

The Java payment core calls this internally. The Python service returns `APPROVE`, `STEP_UP`, or `DECLINE` with a numerical risk score.
