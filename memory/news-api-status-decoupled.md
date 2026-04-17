---
name: News API status vs POST rate limit are decoupled
description: /api/status canFileSignal=true does NOT guarantee signal POST will succeed — separate rate limiters
type: feedback
---

`GET /api/status` returning `canFileSignal: true` with `waitMinutes: null` does not guarantee `POST /api/signals` will succeed. The POST endpoint has its own independent rate limit.

**Why:** Observed 2026-04-17 — status showed eligible, POST returned 429 "34 minutes remaining." Two separate systems.

**How to apply:** Always handle 429 on the signal POST regardless of what status says. Use `lastNewsFiledAt` in state as the authoritative cooldown clock. Cache signal on 429, retry next run.
