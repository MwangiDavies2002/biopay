# Security model

## Core rules

1. **No raw remote fingerprint transmission.** For phones/laptops, use WebAuthn/passkeys so the OS biometric subsystem unlocks a device-held private key.
2. **No ordinary fingerprint hash matching.** Fingerprint captures vary between scans. Dedicated reader integrations must use protected biometric templates and a vetted matcher/SDK.
3. **Transaction binding.** Authorization must cover payment ID, merchant, exact amount/currency, nonce and expiry.
4. **Replay protection.** A nonce is one-time-use and expires quickly.
5. **Liveness for dedicated readers.** A fingerprint match alone is insufficient for high-trust payment authorization.
6. **Risk controls.** Amount, device, transaction velocity, merchant risk, failed attempts and anomaly signals should influence approval/step-up decisions.
7. **Fallback authentication.** Recovery cannot simply bypass security; use controlled recovery/step-up mechanisms.
8. **Financial atomicity.** Debit and credit ledger records must be written in one DB transaction.
9. **Least privilege.** The risk service cannot mutate balances.
10. **Auditability.** Authentication, risk and payment state transitions require immutable audit references.

## Remote WebAuthn target flow

```text
1. Merchant creates payment request.
2. Server creates nonce/challenge and expiry.
3. Customer device displays merchant + amount.
4. OS performs biometric/PIN verification locally.
5. Device private key signs the challenge-bound assertion.
6. Server verifies credential public key, challenge, origin/RP ID, counter/metadata as applicable.
7. Risk engine evaluates context.
8. Payment core atomically posts debit and credit.
9. Nonce is consumed and cannot be replayed.
```

## Dedicated POS fingerprint target flow

```text
reader -> liveness -> protected template/matcher -> user/credential result -> signed local device assertion -> payment core
```

Prefer certified hardware/SDKs with device attestation. Avoid implementing a biometric matcher from scratch for production.

## Prototype shortcut

`BIOPAY_DEMO_MODE=true` permits `/demo-authorize`, which simulates successful local biometric/passkey verification. This endpoint is strictly for the local proof-of-concept and must not exist in a production profile.
