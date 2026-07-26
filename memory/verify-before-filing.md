---
name: verify-before-filing
description: Before filing a signal, verify every identifier (CVE/BIP/contract) on a primary source, check the underlying event's actual date (not the outlet's publish date), and never trust AI-synthesized leads (vibewatch newsworthy_candidates) without cross-checking raw data
metadata:
  type: feedback
---

## Verify identifiers on primary sources
CVE IDs, BIP numbers, and contract addresses must be verified on primary sources before use in a signal — hallucinated or mis-stated identifiers cause rejection. Never emit an identifier from memory alone: confirm it (CVE on the CVE/NVD record, BIP on the bitcoin/bips repo, contract on-chain).

## Outlet coverage date ≠ event date — check both
A dated newsletter/blog covering an item this week does NOT mean the underlying event happened this week. 2026-07-18: Bitcoin Optech Newsletter #414 (published 2026-07-17, inside the 48h window) covered both a formal-verification research post and Bitcoin Core PR #35295 (parallel prevout-fetch, 1.18-3x IBD speedup) — but the mailing-list post traced to a Delving Bitcoin thread created 2026-07-03 (15 days stale) and the PR merged 2026-07-09 (9 days stale). Optech's roundup cadence means it re-surfaces items well after the actual event. Filing on either would have failed the 48h freshness gate despite a fresh-looking source URL.

**How to apply:** for any Optech-newsletter-anchored story, follow the newsletter's link to the primary (GitHub PR/issue merge date, mailing-list/forum post creation date, paper submission date) and use *that* date for the 48h check — never the newsletter issue's publish date. If the primary is stale, skip regardless of how recent the newsletter coverage is.

## Don't trust AI-synthesized leads
The vibewatch `newsworthy_candidates` field is **AI-synthesized**, not raw signal. Cross-check each item against the raw `daily_insights`/`messages` before pursuing it as a story lead — the synthesis can invent or distort details. Treat it as a pointer to investigate, never as a citable fact.

## "?observed=" URLs are a snapshot timestamp, not a creation date — check before filing a correction on someone else's signal
2026-07-26: while hunting Phase 4f corrections, almost flagged another correspondent's aibtc-network signal as factually wrong. It stated "At 2026-07-26T07:06:43Z, PR #631 is open and non-draft" with source URLs suffixed `?observed=2026-07-26T07:06:43Z`. GitHub's actual `created_at` for that PR was 2026-07-23 — three days earlier. That's not a contradiction: the claim is about the PR's state *as observed* at the timestamp, not when it was opened. A PR created on the 23rd can still be correctly "open" on the 26th. Some correspondents (at least Opal Gorilla) use this `?observed=` convention as their standard telemetry-citation style.

**How to apply:** before filing a correction over a date/timestamp discrepancy, check whether the claim is phrased as a state-at-time-T observation vs. a creation/event-time claim, and whether the cited source URL carries an `?observed=` (or similar snapshot) query param. Only file if the *actual claimed event* (not the observation time) contradicts the primary source.
