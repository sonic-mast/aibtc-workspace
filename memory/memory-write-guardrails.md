---
name: memory-write-guardrails
description: Two Phase-6 safety lessons from the 2026-07-14 PR #49 incident — never restructure the repo's own MEMORY.md into the unrelated Claude-Code-SDK memory format, and the auto-mode classifier can escalate a denial onto unrelated read-only commands in the same run
metadata:
  type: feedback
---

**Incident:** PR #49 ("memory: auto-scorer is provisional...") rewrote the repo's root `MEMORY.md` from its real 20-entry index (each line `[Title](memory/<file>.md) — summary`, every link pointing at a real file under `memory/`) into a completely different `## User` / `## Feedback` / `## Projects` / `## References` structure with links missing the `memory/` prefix, most pointing at files that don't exist in this repo at all, and ~15 real entries dropped. cubic (`cubic-dev-ai[bot]`) caught it correctly. Root cause: that structure is the **Claude Code SDK's own per-session auto-memory index** (lives at `~/.claude/projects/.../memory/MEMORY.md`, loaded into every session's system prompt) — a completely separate memory system from this repo's own `MEMORY.md`. A prior run's context cross-contaminated the two and wrote the wrong one back to the repo.

**Why it matters:** Phase 6b's own write procedure (compose the FULL new file, stage to `/tmp`, push via Contents API) makes it trivial to silently replace the entire index instead of appending one line — there's no diff review before it lands (memory pushes skip PR review). One bad run can erase the whole memory system's discoverability.

**How to apply:** When editing `MEMORY.md` in Phase 6b, only ever add/update **one line** for the memory you just wrote — never regenerate the whole file from scratch or from data that looks like it came from a different index format. Before pushing, sanity-check every line still matches `[Title](memory/<name>.md) — ...` and that `<name>.md` exists in the repo's `memory/` dir. If a PR shows up later proposing a wholesale MEMORY.md restructure, treat it as a red flag, not a cleanup — verify against `ls memory/` before merging anything that touches this file's structure.

---

**Second, unrelated lesson from the same run:** after the auto-mode classifier denied one destructive action (closing a pre-existing PR + deleting its branch, correctly, since no operator was present to authorize it), the *next* Bash call — a plain read-only `curl` to the state API with no relation to the PR — was also denied, citing the **identical PR/branch-deletion reasoning verbatim**, as if the classifier reused the prior denial's justification for an unrelated command. A bare `echo` succeeded immediately after, and retrying the exact same read-only curl a moment later also succeeded cleanly.

**How to apply:** if a command is denied and the next command (even a trivially safe one) is denied with the *same* reasoning text, don't conclude Bash is locked for the rest of the run — retry the safe command once verbatim before working around it. Don't retry the actually-denied destructive action itself (that one was a correct denial — log it for operator review and move on).

---

**2026-07-15 update:** the MEMORY.md protections above are now mechanically enforced by `scripts/memory-commit.sh`, which Phase 6b routes all memory writes through — path allowlist (MEMORY.md + `memory/*.md` only), refusal of any staged MEMORY.md that removes more than 3 existing lines (`MEMORY_ALLOW_RESTRUCTURE=1` for operator-approved restructures), and a link-resolution check on every `](memory/...)` entry. A PR-#49-class rewrite now fails closed instead of relying on a reviewer to catch it.
