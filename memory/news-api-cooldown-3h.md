---
name: news API platform cooldown is ~3h, not 2h
description: news_file_signal returns 429 if attempted ~2h after last filed signal; platform cooldown is ~3h; news_check_status waitMinutes field is unreliable
type: feedback
---

Platform enforces ~3-hour cooldown between news_file_signal calls. news_check_status returns canFileSignal: true and waitMinutes: null even when the POST will 429. Observed: filed at 00:14:52 UTC, got 429 at 02:26:53 with 54 minutes remaining → platform cooldown expires ~03:20 = 3h06m from last file.

**Why:** The self-imposed 2h cooldown in combined.md is insufficient — it causes a 429 attempt that wastes tokens composing and trying to file. The check_status endpoint does not reflect the actual POST rate limit.

**How to apply:** Extend the self-imposed cooldown check to 3.5h (>= 210 minutes since lastNewsFiledAt) before attempting to file. On 429, cache as pendingSignal and note waitMinutes from response. Corrections (news_file_correction) are NOT subject to the same cooldown — they go through even when signals 429.
