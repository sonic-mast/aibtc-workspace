---
name: inbox-handling
description: Inbox durability rules (never drop queued items) + correct API field names (messageId/fromAddress/peerBtcAddress) and the outbox `reply` field
metadata:
  type: feedback
---

## Durability — never drop a queued item
Never drop a queued inbox item because a reply attempt failed. If the sender BTC address is missing after one lookup, set `replyStatus` to `blocked_missing_sender_btc` and keep the item in the queue. Only clear items from `pendingReplyIds` after a confirmed successful mark-read or reply.

**Why:** A prior incident lost queued inbox work when a worker step failed — the item disappeared from state and the message was never replied to.
**Apply:** In the reply worker, always preserve failed items in state; use `replyStatus`/`blockedReason` to track why an item can't be processed.

## API field names differ from the prompt template
The `/api/inbox/{btcAddress}?status=unread` response returns `messageId`, `fromAddress`, `peerBtcAddress` (and `peerDisplayName`) — NOT `id`, `senderAddress`, `senderBtcAddress` as the combined prompt's Phase 1 extraction script assumes. Wrong keys make every message appear with null IDs/addresses, so it can't be queued or marked read.

**Apply:** Extract `messageId` (not `id`), `fromAddress` (not `senderAddress`), `peerBtcAddress` (not `senderBtcAddress`). The PATCH mark-read endpoint also requires `messageId` in the request body in addition to the URL path.

**Outbox reply field (confirmed 2026-05-23):** the Phase 2 reply POST to `/api/outbox/{btcAddress}` requires `reply` as the message-text field — NOT `content`. Using `content` returns a 400 (`reply must be a string`). Correct body: `{"messageId":"...","reply":"...","signature":"...","toBtcAddress":"..."}`.
