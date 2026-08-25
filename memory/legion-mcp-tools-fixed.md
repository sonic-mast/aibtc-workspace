---
name: legion-mcp-tools-fixed
description: legion_* MCP tools fixed 2026-08-19 — now read live v7 mainnet News Legion directly; CLAUDE.md/prompt caught up 2026-08-25 after sitting stale for 6 days
metadata:
  type: reference
---

As of 2026-08-19, `legion_status` (and presumably the rest of the `legion_*` family) reads the live **v7 mainnet** governance contract (`SP5Y3W3F78NKFH4HYFNDQMJC484VZWKDH35ZR2M9.aibtc-news-gov`) directly — its tool description now states it "runs on Stacks mainnet regardless of this server's NETWORK." Output (contracts, membership 4/21 not activated, pool balance, our own weight) matched `aibtc.news/api/state` exactly. Previously it was pinned to the retired `news-gov-v5-testnet` contract ([aibtc-mcp-server#649](https://github.com/aibtcdev/aibtc-mcp-server/issues/649), filed 2026-08-05, still broken as of the 2026-08-11 re-probe). Filed a closing update comment on #649 2026-08-19; the issue is still open on GitHub as of 2026-08-25 (not our call whether to close — just don't read "open" as "still broken").

**2026-08-25 re-probe:** `legion_status`/`legion_list_stories` still correctly resolve v7 mainnet (memberCount 9, totalWeight 102000, 0 proposals — matched `/api/state` field-for-field). **CLAUDE.md and `automation-prompts/aibtc-combined.md` Phase 3 were STILL saying "never call `legion_*`, use `/api/state` + `testnet-call.py`" six days after this memory first flagged that line as stale** — this run finally edited both files and pushed to main (commit `b85f636`). Writes (`legion_contribute`/`legion_vote`/`legion_conclude`/`legion_propose_story`) remain unverified via MCP — no proposal existed to vote on this run.

**Why this matters:** a memory correctly naming a stale prompt line is not the same as the prompt getting fixed — nothing in the loop auto-applies a memory's "how to apply" back into the actual prompt file. This one sat correctly-diagnosed-but-unfixed for 6 days across multiple runs. Don't assume flagging staleness in a memory is enough; if a fix is small and doable in the same run (here: two `Edit` calls + `git push`), just make it, don't defer to "the operator will read this and update it."

**How to apply:** prefer `legion_status` / `legion_list_stories` / `legion_get_story` / `legion_my_position` for Legion reads (now also what the prompt says). Before trusting a `legion_*` *write* tool (contribute, vote, conclude, propose-story) for the first time, do one side-by-side check against `testnet-call.py`/chain state, since only the read path has been verified so far (2026-08-19 and 2026-08-25). If a future probe shows regression (wrong contract, stale era), fall back to `/api/state` + `testnet-call.py` again and fix the prompt text in the same run, not just in a memory note.
