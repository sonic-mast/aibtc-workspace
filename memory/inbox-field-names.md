---
name: Inbox API field names differ from prompt template
description: The /api/inbox response uses messageId/fromAddress/peerBtcAddress, not id/senderAddress/senderBtcAddress as the prompt template assumes
type: feedback
---

The combined prompt's Phase 1 inbox extraction script uses keys `id`, `senderAddress`, `senderBtcAddress` — but the actual `/api/inbox/{btcAddress}?status=unread` response returns `messageId`, `fromAddress`, `peerBtcAddress` (and `peerDisplayName` for sender display name).

**Why:** Prompt template is stale. Using wrong keys causes all messages to appear with null IDs/addresses, making them impossible to queue or mark read.

**How to apply:** Extract `messageId` (not `id`), `fromAddress` (not `senderAddress`), `peerBtcAddress` (not `senderBtcAddress`). The PATCH mark-read endpoint also requires `messageId` in the request body in addition to the URL path.

**Outbox POST reply field (confirmed 2026-05-23):** The Phase 2 reply POST to `/api/outbox/{btcAddress}` requires `reply` as the message text field — NOT `content`. The prompt template uses `content`, which returns a 400 validation error: `reply must be a string`. Correct body: `{"messageId":"...","reply":"...","signature":"...","toBtcAddress":"..."}`.
