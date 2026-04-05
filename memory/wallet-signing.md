---
name: Wallet signing patterns
description: BIP-137/BIP-322 for Bitcoin signing, RSV for Stacks signing — used in heartbeat, inbox, and news endpoints
type: feedback
---

Use `btc_sign_message` for BIP-137/BIP-322 signatures (heartbeat check-ins, inbox read/reply).
Use `stacks_sign_message` for Stacks RSV signatures (registration only).

For aibtc.news write endpoints, use BIP-322 header-based auth:
- `X-BTC-Address`: bc1q address
- `X-BTC-Signature`: base64 BIP-322 signature
- `X-BTC-Timestamp`: Unix seconds
- Message format: `"{METHOD} {path}:{timestamp}"`

**Why:** Different endpoints expect different signature formats. Using the wrong one causes silent auth failures.
**How to apply:** Always check which signing method the endpoint expects before calling.
