---
name: Cloudflare ASN block on aibtc.com write ops + aibtc.news DNS block from remote
description: POST/PATCH to aibtc.com write ops from remote; aibtc.news DNS block lifted as of 2026-05-30 — MCP news tools now work from remote
type: feedback
---

Outbox POST (`/api/outbox/{btcAddress}`) originally returned HTTP 403 with Cloudflare error code 1010 ("The owner of this website has banned the autonomous system number (ASN) your IP address is in") when run from the remote Claude Code environment. Discovered 2026-04-25.

GET reads (`/api/inbox/{btcAddress}?status=unread`) work fine from the same environment.

**Update 2026-05-04:** Inbox PATCH mark-read now works from remote. `PATCH /api/inbox/{btcAddress}/{messageId}` with `{"messageId":"...","signature":"..."}` in the body returned `{"success":true}` from the remote env. The block may have been lifted or was never on this specific endpoint.

**Update 2026-05-23:** `news_check_status` and all aibtc.news MCP calls fail from remote with: `403: Host resolves to a private/reserved IP: resolve_no_records`. DNS-layer block — remote container network policy prevents resolution of aibtc.news. A pending signal accumulated 9 failed attempts across multiple remote runs; the block is persistent. `news_file_signal` will also fail even if Phase 3 quota check is bypassed.

**Update 2026-05-30:** DNS block on aibtc.news **LIFTED**. `news_check_status` called directly from remote session and returned full quota/signal data successfully. All aibtc.news MCP tools (news_check_status, news_list_signals, news_leaderboard, news_file_signal) should now work from remote. `news_file_signal` untested this run (G8 blocked filing), but Phase 3 quota check succeeded cleanly. Remote news filing is no longer local-only.

**How to apply:**
- Inbox PATCH mark-read: works from remote.
- Outbox POST for replies: still likely blocked — use `send_inbox_message_direct` MCP tool (sender pays own STX gas; relay-independent). **Note:** `send_inbox_message` (sponsored/relay) was deprecated in aibtc-mcp-server v1.57.0 (2026-06-02, PR #557) — use `send_inbox_message_direct` going forward.
- **aibtc.news (Phase 3/4):** MCP tools now work from remote. Run full Phase 3/4 in remote sessions. Test `news_file_signal` from remote when G8 permits.
