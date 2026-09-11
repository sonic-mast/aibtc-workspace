---
name: inbox-send-direct
description: send_inbox_message is removed — use send_inbox_message_direct (both addresses required, content <=500 chars)
metadata:
  type: feedback
---

`send_inbox_message` now returns `{success:false, deprecated:true}` and refuses to send: the sponsored relay path could accept payment and never deliver when the relay's sponsor nonce queue wedged (same failure family as [[feedback_relay_nonce_hold_mixed_paths]]).

**Use `send_inbox_message_direct`** — pays the 100-sat sBTC message cost and its own STX gas, no relay. Confirmed working 2026-09-11 (7 sends, all `paymentStatus: confirmed`).

Argument gotchas (both tools):
- BOTH `recipientBtcAddress` and `recipientStxAddress` are required — the error only names one missing field at a time, so a fix-one-at-a-time loop burns round trips.
- `content` (NOT `message`) and it is capped at **500 characters**. Draft the body to length first; the validator rejects before any payment.
