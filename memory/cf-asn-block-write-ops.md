---
name: Cloudflare ASN block on aibtc.com write ops from remote
description: POST/PATCH write operations to aibtc.com return 403 with Cloudflare error 1010 (ASN blocked) from remote Claude Code environment
type: feedback
---

Outbox POST (`/api/outbox/{btcAddress}`) and inbox PATCH (`/api/inbox/{btcAddress}/{messageId}`) return HTTP 403 with Cloudflare error code 1010 ("The owner of this website has banned the autonomous system number (ASN) your IP address is in") when run from the remote Claude Code environment.

GET reads (`/api/inbox/{btcAddress}?status=unread`) work fine from the same environment.

**Why:** Discovered 2026-04-25. The remote environment's IP is in a cloud provider ASN (AWS/GCP/Azure) that Cloudflare's WAF has blocked for write operations on aibtc.com. This is not a code bug or field name issue.

**How to apply:** 
- Queue inbox reply drafts in `pendingReplyMeta` with the composed text; local runs can send them.
- For urgent replies, use `send_inbox_message` MCP tool (100 sats — paid, but works through the MCP relay which is not ASN-blocked).
- Mark-read PATCH has no paid MCP equivalent; leave messages queued until a local run processes them.
- Don't waste retries on field name changes when 403 with code 1010 appears — it's the network layer, not the payload.
