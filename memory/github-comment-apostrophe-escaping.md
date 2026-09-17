---
name: github-comment-apostrophe-escaping
description: A prior run posted a public GitHub comment with apostrophes mangled into literal triple-quotes (I'''m, That'''s, Doesn'''t) — sanitize text before posting via curl/bash
metadata:
  type: feedback
---

A live public comment (aibtcdev/legions#12, comment id 5705822018, posted 2026-09-16T23:09:02Z) shipped with every apostrophe rendered as three single quotes: "I'''m a prior data point", "That'''s the same channel", "Doesn'''t change your ceiling math", "isn'''t 'try harder'", "haven'''t been personally asked". Readable but visibly broken — the kind of thing a human reader notices immediately in Sonic Mast's own voice.

**Why:** whatever run composed that comment ran the reply text through a shell step that escaped `'` as `'\''` or similar inside a single-quoted string, and something in the chain (likely a `python3 -c "..."` wrapping a single-quoted body, or a `curl -d '...'` with embedded apostrophes) doubled or tripled the escape instead of resolving it. The bug is in the posting path, not in my composition — the source text was presumably normal English.

**How to apply:** when composing a GitHub comment/PR body with a bash heredoc or `-d`/`-c` payload that contains apostrophes, prefer writing the body to a temp file first (`Write` tool or `cat <<'EOF' > /tmp/body.txt`) and passing `--data @/tmp/body.txt` or `-f body=@/tmp/body.txt`, rather than inlining the string through nested shell quoting. Before posting any comment, sanity-check the rendered string for stray repeated quote characters. This comment was not edited (out of scope for the automated loop — GitHub comment edits aren't in the combined prompt's action list), so it's flagged here for the operator to fix by hand if desired.
