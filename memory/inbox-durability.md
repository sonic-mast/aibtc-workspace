---
name: Inbox durability rules
description: Never drop queued inbox items — block them with a reason instead of removing on failure
type: feedback
---

Never drop a queued inbox item because a reply attempt failed. If sender BTC address is missing after one lookup, set `replyStatus` to `blocked_missing_sender_btc` and keep the item in the queue.

Only clear items from `pendingReplyIds` after a confirmed successful mark-read or successful reply.

**Why:** A prior incident where queued inbox work was lost because a worker step failed. The item disappeared from state and the message was never replied to.
**How to apply:** In the reply worker, always preserve failed items in state. Use `replyStatus` and `blockedReason` fields to track why an item can't be processed.
