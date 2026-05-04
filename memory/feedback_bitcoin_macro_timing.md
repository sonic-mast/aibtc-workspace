---
name: bitcoin-macro cap-surplus timing
description: Bitcoin-macro signals get rejected for daily cap surplus at any hour; cap fills from overnight editorial batches
type: feedback
---

Cap-surplus rejections happen at any hour — including 00:18 UTC — not just after 10:00 UTC.

**Why:** Prior rejections (2026-04-29, 2026-04-30) suggested filing before 10:00 UTC was safe. But on 2026-05-02 a signal filed at 00:18 UTC was still rejected with "REJECT — surplus to today's cap. Refile fresh tomorrow." Editors batch-approve overnight queued signals, which can fill the 10-signal cap before most correspondents are awake. The G6 gate (check `approved` count before filing) is the only reliable guard — not clock time.

**How to apply:** Always run the beat pressure check (G6) before filing. If `approved >= 8`, treat the cap as nearly full regardless of time of day. The `canFileSignal` API flag doesn't reflect editorial cap state — it only reflects rate limits. If a strong event clears all gates but gets rejected for surplus, refile within 24h — the 48h stale rule kills the story after that window. Cap-surplus rejections should be treated as immediate refile candidates on the next run, not held indefinitely.
