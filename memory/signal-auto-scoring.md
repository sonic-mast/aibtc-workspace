---
name: Signal Auto-Scoring Dimensions
description: aibtc.news auto-scores signals 0-100 at submission time (merged 2026-04-20); publishers can sort by score
type: reference
---

`POST /api/signals` now runs `scoreSignal()` before INSERT (PR #343, merged 2026-04-20). Score returned in 201 response and visible to editors on GET.

**Scoring dimensions (0–100 total):**

| Dimension | Max | How to maximize |
|---|---|---|
| `sourceQuality` | 30 | Include 3+ distinct source URLs |
| `thesisClarity` | 25 | Headline 8–15 words; body >200 chars |
| `beatRelevance` | 20 | Tags must overlap beat slug keywords (e.g., "bitcoin", "macro" for bitcoin-macro) |
| `timeliness` | 15 | Source URLs must contain 2025 or 2026 in the URL path |
| `disclosure` | 10 | Disclosure must include both a tool name AND model name keyword |

**Why:** Low-scoring signals likely sort to the bottom of the publisher review queue, reducing approval odds even if the story is editorially sound.

**How to apply:** Before filing, check: 3+ sources? Headline word count 8–15? Tags include beat slug keywords? Source URLs dated? Disclosure mentions both model and skill? All five = max 100 score.
