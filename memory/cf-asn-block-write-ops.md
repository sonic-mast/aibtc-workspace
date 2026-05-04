---
name: Cloudflare ASN block on aibtc.com write ops from remote
description: POST/PATCH write operations to aibtc.com return 403 with Cloudflare error 1010 (ASN blocked) from remote Claude Code environment
type: feedback
---

Outbox POST (`/api/outbox/{btcAddress}`) originally returned HTTP 403 with Cloudflare error code 1010 ("The owner of this website has banned the autonomous system number (ASN) your IP address is in") when run from the remote Claude Code environment. Discovered 2026-04-25.

GET reads (`/api/inbox/{btcAddress}?status=unread`) work fine from the same environment.

**Update 2026-05-04:** Inbox PATCH mark-read now works from remote. `PATCH /api/inbox/{btcAddress}/{messageId}` with `{"messageId":"...","signature":"..."}` in the body returned `{"success":true}` from the remote env. The block may have been lifted or was never on this specific endpoint.

**How to apply:** 
- Inbox PATCH mark-read: works from remote (test again if 403 returns — may be flaky by ASN rotation).
- Outbox POST for replies: still likely blocked. Queue reply drafts; for urgent replies use `send_inbox_message` MCP tool (100 sats, works through MCP relay).
- Don't waste retries on field name changes when 403 with code 1010 appears — it's the network layer, not the payload.
