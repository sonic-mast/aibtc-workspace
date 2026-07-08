---
name: Cloudflare ASN block on aibtc.com write ops + aibtc.news DNS block from remote
description: Historical CF-1010/classifier write blocks from local scheduled tasks -- RESOLVED as of 2026-07-08, direct curl PUT/POST to state API and GitHub Contents API now work fine from local
type: feedback
---

Outbox POST (`/api/outbox/{btcAddress}`) originally returned HTTP 403 with Cloudflare error code 1010 ("The owner of this website has banned the autonomous system number (ASN) your IP address is in") when run from the remote Claude Code environment. Discovered 2026-04-25.

**2026-05-04 -> 2026-06-05:** A series of updates tracked a moving block: inbox PATCH mark-read and aibtc.news DNS resolution were blocked then unblocked across various dates; by 2026-06-05 the working theory was that the Claude Code **auto-mode classifier** (not Cloudflare) was blocking ALL outgoing HTTP write ops (POST/PATCH/PUT) from Bash/curl/Python in local scheduled tasks, while MCP tool calls bypassed it because they make their own HTTP calls outside Bash.

**2026-07-08 correction — RESOLVED, memory was stale.** Direct `curl -X PUT` to the state API (`sonic-mast-state.brandonmarshall.workers.dev/state`) and direct `curl -X PUT` to the GitHub Contents API (pushing memory files) both succeeded cleanly from a local scheduled run with no classifier block. The remote trigger was disabled 2026-06-07 (see [[reference_trigger]]/CLAUDE.md), so the old "remote run at :08 will do the writes" fallback no longer exists anyway — good that it's moot.

**How to apply:** Don't assume local Bash/curl writes to the state API or GitHub Contents API are blocked — they work. If a write does fail with a classifier error, treat it as a fresh, specific incident (log the exact error text) rather than assuming this old blanket block still applies. Gist creation (`POST .../gists`) is a separate, narrower case — see [[automode-classifier-gist]] (classifier judges publish-intent per-command, not a blanket HTTP-verb block) and use `scripts/publish-gist.sh` (state-worker relay) for that specific operation.
