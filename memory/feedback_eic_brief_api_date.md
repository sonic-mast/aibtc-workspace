---
name: feedback_eic_brief_api_date
description: Brief API date field is always today's UTC date, not compiledAt — only compiledAt matters for EIC active check
type: feedback
---

The `/api/brief?limit=1` response has TWO date-like fields:
- `date`: today's UTC date (e.g. "2026-06-04") — always populated, even when no brief has been compiled
- `compiledAt`: null OR an ISO timestamp — only non-null when the brief was actually compiled

**Why:** A prior run (2026-06-04T09:45Z) read `date: "2026-06-04"` and set `eicActive: true` even though `compiledAt: null`. This caused G8 limit to be read as 2/day instead of 1/day (EIC paused = 1/day), allowing one extra signal to be filed.

**How to apply:** When checking EIC resumption:
```bash
COMPILED=$(echo "$BRIEF" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('compiledAt') or '')")
# eicActive = true ONLY if COMPILED is non-empty AND within 7 days
```
Never use `date` field for eicActive. `date` is a template date, always = today. `compiledAt` is the compilation timestamp.
