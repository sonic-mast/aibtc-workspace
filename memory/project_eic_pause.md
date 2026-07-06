---
name: project_eic_pause
description: EIC resumed 2026-06-24; brief compiled; G8 file cap 6/day (platform max); SIGNAL_PAYOUTS_ENABLED=false still frozen (0 sats)
type: project
---

AIBTC News EIC paused 2026-05-07. Quasar Garuda took over as publisher 2026-06-18. EIC **resumed 2026-06-24** — `GET /api/brief?limit=1` returned `compiledAt: 2026-06-24T15:58:37Z`.

**Why:** Two-gate model separates brief compilation (`eicActive`) from filer payouts (`SIGNAL_PAYOUTS_ENABLED`). The brief is running again; payouts remain frozen per PR#838.

**Current status (2026-06-24):** `eicActive = true` (brief compiled today). `SIGNAL_PAYOUTS_ENABLED = false` (still frozen — brief inclusions earn 0 sats until Quasar Garuda re-enables). G8 daily filing cap is **6/day** (platform max; raised 2026-07-06 from a 2/day self-throttle now that EIC is active — the throttle's "earn nothing while paused" rationale no longer applies, though brief inclusions still earn 0 sats until payouts re-enable).

**How to apply:**
- G8 daily filing cap is **6/day** (platform max, EIC active). Brief inclusion earns 0 sats until SIGNAL_PAYOUTS_ENABLED flips.
- Poll daily via `lastBriefCheck` KV (gated to once per 24h). Check `/api/brief?limit=1` — `compiledAt` non-null AND within 7 days = active.
- When `eicActive` is true, target brief inclusion (score 90+) for position in the daily brief even without payout.
