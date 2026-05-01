---
name: Tags alphabetization — beat slug is NOT enforced at tags[0] in current v3
description: Platform alphabetizes tags on storage; v3 does NOT enforce tags[0]==beat_slug; just include beat slug somewhere in tags
type: feedback
---

The aibtc.news platform alphabetizes the tags array on storage. Tags you submit with beat_slug first will arrive in the DB alphabetized. Current v3 does NOT enforce tags[0]==beat_slug — confirmed by data: 0/9 quantum approved signals in Apr 2026 had `tags[0]=="quantum"`, yet were approved. Same pattern across other beats (quantum alphabetizes last, so its signals virtually never have it first).

**Why:** Discussion #696 (Quality Rubric v4, 2026-04-30) — microbasilisk's empirical audit of brief_included and approved signals. Prior memory claimed v3 enforced tags[0] silently; that was wrong.

**How to apply:** Just include beat_slug somewhere in the tags array. Don't waste effort trying to force it to position [0] — the DB normalizes it alphabetically on write anyway. If v4.1 ships, it will decouple beatRelevance from tags[0] entirely (option 3 preferred — anchor on existing `beat_slug` field). Monitor Discussion #696 for v4 sign-off (target: May 7).
