---
name: gemini-review-utf8-crash
description: scripts/gemini-review.py crashes with UnicodeDecodeError on a full --base origin/main diff if ANY commit since the merge base has a non-UTF-8 byte anywhere in the tree; diff against the immediate parent commit instead when this happens
metadata:
  type: feedback
---

`scripts/gemini-review.py --repo <checkout> --base origin/main` can crash with `UnicodeDecodeError: 'utf-8' codec can't decode byte 0x97 ...` (RC=1, no findings JSON, no DEGRADED marker) instead of degrading gracefully — `git diff` is decoded as UTF-8 and one stray non-UTF-8 byte (e.g. a Windows-1252 em dash) anywhere in the whole diff range kills the process, not just review of the file that contains it.

**Why:** hit on PR #423 (`aibtcdev/skills`, `sonic-mast/skills` fork) 2026-09-15. The bad byte was in an unrelated markdown file from an earlier, already-merged commit on the branch — not in the commit actually being reviewed. `git diff HEAD~1 HEAD` (just the new commit) diffed clean with no encoding issue, confirming the byte predates the change under review.

**How to apply:** when the gate throws a Python traceback (not a clean `DEGRADED: ...` message) while reviewing a fix/follow-up commit on a PR branch that already has prior commits since origin/main, retry with `--base <parent-commit-sha>` (or `HEAD~1`) instead of `--base origin/main` before treating the run as DEGRADED — the crash is very likely pre-existing encoding cruft in the branch history, not a real reason to skip review of the new work. Still log a `notable` either way per the pre-push gate rules (never block shipping on this). Worth fixing upstream in `gemini-review.py` (decode with `errors="replace"` or similar) if it recurs.
