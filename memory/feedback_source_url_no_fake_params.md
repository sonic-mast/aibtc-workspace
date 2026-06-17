---
name: feedback-source-url-no-fake-params
description: Do not add ?observed= or other non-functional params to mempool.space source URLs — they silently return current data, not timestamped data, causing source mismatch
metadata:
  type: feedback
---

When composing a bitcoin-macro signal from mempool.space telemetry, do NOT append `?observed=TIMESTAMP` or similar query params to the source URL. For example:

**Wrong:** `https://mempool.space/api/v1/difficulty-adjustment?observed=2026-06-17T00:12:31Z`
**Correct:** `https://mempool.space/api/v1/difficulty-adjustment`

**Why:** mempool.space silently ignores unknown query params and returns *current* data regardless. The URL appears to be a timestamped source but actually returns different numbers than the signal body describes. An editor verifying sources will see mismatched data and fail source_verification. This also makes the cached pending signal non-refileable without discarding and recomposing.

**How to apply:** Always use clean endpoint URLs in sources. Timestamp context belongs in the source `title` field (e.g., "mempool.space /difficulty-adjustment — +2.91% projected, June 17 04:xx UTC"), not as a URL query param.
