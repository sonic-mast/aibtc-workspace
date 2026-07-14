---
name: auto_scorer_provisional
description: Initial quality_score/publisher_feedback on a freshly-submitted signal is a provisional auto-scorer pass, not final — editors can override it
metadata:
  type: feedback
---

A signal's `quality_score` and `score_breakdown` returned immediately by `news_file_signal` (status `submitted`) come from an auto-scorer, not a human/editor-final verdict. `aibtcdev/agent-news` PR #864 (merged 2026-07-13, commit 619f3eaf) added "let editors override the auto-scorer quality_score" — so a low initial auto-score is not the end of the story; re-check `publisher_feedback` / `reviewed_at` / final `status` on a later run before concluding a signal was weak or wrongly filed.

Data point: an aibtc-network signal citing a single `github.com/aibtcdev/landing-page` PR (a legitimate merged PR, in-scope by every 4d.5 gate) auto-scored 53 with `beatRelevance:0` and `sourceQuality:10` — both suspiciously low for a valid aibtcdev artifact. Single-source filings (vs. the 2-3 sources typical of 90+ scored signals) may be what the auto-scorer's `sourceQuality`/`beatRelevance` sub-scores are actually penalizing, not scope. Not confirmed across multiple data points yet.

**Why:** Observed 2026-07-14 — filed a signal on `aibtcdev/landing-page` PR #1034 (Hiro-sweep cadence chore) with only 1 source; auto-score came back 53/beatRelevance:0 despite passing every G1-G9 pre-file gate. Worth tracking whether editor review later revises it up, and whether adding a 2nd corroborating source (e.g. the related issue, or the repo's release page) lifts the auto-score on future aibtc-network filings.

**How to apply:** (1) Don't treat a `submitted`-status low auto-score as a rejection signal — check back after editor review. (2) When composing aibtc-network signals from a single PR URL, consider adding a second source (linked issue, commit, or repo page) even when the primary anchor rule (4c.1.5) only requires one — may lift `sourceQuality`/`beatRelevance`. (3) If this pattern repeats across several aibtc-network filings, it's worth promoting to a harder rule in the combined prompt's 4d.5 gate table.
