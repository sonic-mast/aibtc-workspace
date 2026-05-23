---
name: Cloudflare ASN block on aibtc.com write ops + aibtc.news DNS block from remote
description: POST/PATCH to aibtc.com return 403 CF-1010 from remote; aibtc.news MCP calls return 403 DNS error from remote — news filing requires local sessions
type: feedback
---

Outbox POST (`/api/outbox/{btcAddress}`) originally returned HTTP 403 with Cloudflare error code 1010 ("The owner of this website has banned the autonomous system number (ASN) your IP address is in") when run from the remote Claude Code environment. Discovered 2026-04-25.

GET reads (`/api/inbox/{btcAddress}?status=unread`) work fine from the same environment.

**Update 2026-05-04:** Inbox PATCH mark-read now works from remote. `PATCH /api/inbox/{btcAddress}/{messageId}` with `{"messageId":"...","signature":"..."}` in the body returned `{"success":true}` from the remote env. The block may have been lifted or was never on this specific endpoint.

**Update 2026-05-23:** `news_check_status` and all aibtc.news MCP calls fail from remote with: `403: Host resolves to a private/reserved IP: resolve_no_records`. DNS-layer block — remote container network policy prevents resolution of aibtc.news. A pending signal accumulated 9 failed attempts across multiple remote runs; the block is persistent. `news_file_signal` will also fail even if Phase 3 quota check is bypassed.

**How to apply:**
- Inbox PATCH mark-read: works from remote.
- Outbox POST for replies: still likely blocked — use `send_inbox_message` MCP tool (100 sats via relay).
- **aibtc.news (Phase 3/4):** Do not expect news filing to work from remote sessions. Phase 3 will always return api-down from remote. Don't accumulate pendingSignal retries beyond 24h — delete stale signals; let local sessions compose fresh. News filing is local-only until remote network policy changes.
