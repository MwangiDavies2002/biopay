#!/usr/bin/env bash
set -euo pipefail
API="http://localhost:8080/api/v1"

PAYMENT=$(curl -sS -X POST "$API/payment-requests" \
  -H 'Content-Type: application/json' \
  -d '{"payerUserId":"USER-DEMO-001","merchantId":"MERCHANT-DEMO-001","amount":1250,"currency":"KES"}')

echo "$PAYMENT"
PAYMENT_ID=$(python -c 'import json,sys; print(json.load(sys.stdin)["id"])' <<< "$PAYMENT")

curl -sS -X POST "$API/payment-requests/$PAYMENT_ID/demo-authorize" \
  -H 'Content-Type: application/json' \
  -d '{"deviceId":"DEVICE-DEMO-001","liveness":true}'

echo
curl -sS "$API/wallets/USER-DEMO-001"; echo
curl -sS "$API/wallets/MERCHANT-DEMO-001"; echo
