---
name: feedback_cf1010_remote_block
description: CF-1010 ASN block on POST ops to aibtc.com — now affects local runs too, not just remote
type: feedback
---

CF-1010 errors on POST /api/outbox have been observed on BOTH remote runner ASNs AND local runs (2026-06-24: local outbox replies returned 403 CF-1010 error code 1010 on Brandon's machine).

**Why:** Cloudflare WAF/firewall rule blocks certain ASNs or IP patterns from POST operations to aibtc.com. Reads (GET) work; writes (POST) fail. Previously believed to be remote-only but now confirmed on local too.

**How to apply:**
- If outbox replies fail with CF-1010, keep messages in `pendingReplyIds` queue for retry next run.
- Log `notable: "CF-1010 outbox block on local"` so the daily digest surfaces it to the operator.
- Do not skip all write operations — only outbox POST seems affected. news_file_signal (goes via MCP not direct HTTP) still works.
- If persistent across multiple local runs, operator may need to investigate ISP/proxy or Cloudflare settings.
