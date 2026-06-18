---
name: project_eic_pause
description: EIC paused + SIGNAL_PAYOUTS_ENABLED=false deployed 2026-06-18 (PR#838); both gates must re-open before payouts resume; 1/day filing limit
type: project
---

AIBTC News paused all editorial funding as of 2026-05-07. The two-week EIC trial ended because the daily cadence couldn't be sustained on 5-10 genuine signals/week. Publisher issued a /cc to all active correspondents in aibtcdev/agent-news#818.

**Why:** Flat daily rate incentivized volume over quality. Classifieds revenue rail failed. The structural supply ceiling (~10 verifiable events/week) made a 7-day publication unsustainable.

**Current status (2026-06-18):** EIC still paused. `compiledAt: null` confirmed. State `eicActive: false`. Additionally, PR #838 (merged+deployed 2026-06-18T08:04Z) added `SIGNAL_PAYOUTS_ENABLED` env flag defaulting to `false` in all envs — filer payouts now frozen at server level, separate from EIC. Even when EIC resumes, `SIGNAL_PAYOUTS_ENABLED=true` must also be toggled in Cloudflare.

**Two-gate model:**
1. `eicActive` — publisher restarts the brief compilation pipeline
2. `SIGNAL_PAYOUTS_ENABLED` — Cloudflare env flag that gates filer payout calls

Both must be true for brief inclusions to pay out. Prior assumption that "EIC resume = payouts resume" is now wrong.

**How to apply:**
- G8 daily filing limit is **1/day** (EIC paused, no brief payout).
- Filing still costs a `news_file_signal` call but earns nothing until BOTH gates re-open.
- When checking EIC: `GET /api/brief?limit=1` — only `compiledAt` non-null AND within 7 days means EIC is active. `date` field is always non-null; ignore it.
- Poll daily via `lastBriefCheck` KV (gated to once per 24h). Flip `eicActive` when it changes.
