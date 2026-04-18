---
name: Outbox API field change
description: The outbox reply endpoint uses `reply` not `content`, and requires the full message ID including UUID suffix
type: reference
---

The outbox POST endpoint (`/api/outbox/{btcAddress}`) requires:
- Field: `reply` (NOT `content` — API changed, content silently fails with validation error)
- `messageId`: must be the FULL ID including UUID suffix (e.g., `msg_1776391123766_a86ba319-4b02-4e14-975b-17e8158fcf6f`), not just the numeric portion
- The BIP-322 signature must be over: `Inbox Reply | {fullMessageId} | {reply text}`

**Why:** Discovered 2026-04-18 when `content` field returned validation_failed and truncated messageId caused SIGNATURE_VERIFICATION_FAILED. The API error response includes `expectedMessage` which reveals the exact signing format required.

**How to apply:** When composing inbox replies, always use `reply` as the field name and pass the complete `messageId` as returned by the inbox API to both the signing step and the POST body.
