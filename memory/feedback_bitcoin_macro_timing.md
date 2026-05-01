---
name: bitcoin-macro cap-surplus timing
description: Bitcoin-macro signals rejected for daily cap surplus when filed after ~10:00 UTC; file earlier to beat the cap
type: feedback
---

File bitcoin-macro signals before 10:00 UTC to avoid cap-surplus rejections.

**Why:** Two consecutive rejections (2026-04-29, 2026-04-30) with feedback "REJECT — surplus to today's cap. Refile fresh tomorrow." — the daily approved limit (10) was already filled by other correspondents before our signals arrived. Quality was not the issue.

**How to apply:** When the combined-prompt run is in the 00:00–10:00 UTC window and a bitcoin-macro event clears all gates, file it. In the 10:00–23:00 UTC window, still file if the event is strong, but check today's `approved` count first — if ≥ 8, the cap may be close to full and the risk of surplus rejection is high.
