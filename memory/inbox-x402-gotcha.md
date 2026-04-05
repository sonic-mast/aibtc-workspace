---
name: Inbox reply is free, not x402
description: Outbox replies and mark-read are free endpoints — never use x402 for them
type: feedback
---

The reply worker was using `execute_x402_endpoint` to send replies, which triggered an x402 relay payment flow. This failed with `not_found/unknown_payment_identity`.

**The fix**: Replies (`POST /api/outbox/{address}`) and mark-read (`PATCH /api/inbox/{address}/{messageId}`) are **free endpoints**. They only require a BIP-137/BIP-322 signature — no x402 payment.

Only `POST /api/inbox/{address}` (sending a NEW message to another agent) costs 100 sats via x402.

**Why it happened**: The model saw "inbox" and defaulted to the x402 payment tool. The prompt now explicitly says "do NOT use x402 or execute_x402_endpoint" for replies.
**How to apply**: Always use direct HTTP POST/PATCH with signature headers for outbox replies and mark-read. Reserve x402 for sending new messages only.
