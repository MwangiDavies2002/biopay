# BioPay v2 Architecture

## Trust boundaries

```text
Merchant UI ----\
                 >---- Payment Core (Java) ---- MySQL
Customer UI ----/             |                 Redis
                               |
                               +---- Risk/Biometric Service (Python)
```

### Payment Core (system of record)

Responsibilities:

- create payment requests
- bind amount + merchant + payer + nonce + expiry
- validate authorization state
- enforce idempotency/status transitions
- query risk decision
- lock wallets during posting
- post double-entry ledger records atomically
- expose transaction status

The payment core is the only service allowed to change financial balances/ledger state.

### Risk/Biometric Service

Responsibilities:

- receive biometric verification assertions/metadata (not raw fingerprints for remote WebAuthn)
- evaluate liveness result from approved scanner adapters
- evaluate transaction risk signals
- return a bounded risk decision

It does **not** directly debit or credit money.

### Redis

Short-lived data only:

- payment nonce/challenge
- expiry state
- replay-prevention markers
- future rate-limit counters

Redis is not the system of record for balances.

### MySQL

Stores:

- users
- merchants
- wallets
- payment requests
- transactions
- ledger entries
- registered devices/credentials (public credential material only)
- audit/risk event references

Financial changes are committed in one SQL transaction.

## Production evolution

The prototype starts as one Java modular monolith + one Python service. Do not split the Java core into many microservices until scaling or organizational boundaries require it. A later deployment can introduce Kafka/event streaming, HSM-backed signing keys, replicas, read models, reconciliation workers, and settlement connectors while preserving the same financial invariants.
