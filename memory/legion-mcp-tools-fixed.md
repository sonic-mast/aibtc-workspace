---
name: legion-mcp-tools-fixed
description: legion_* MCP tools fixed 2026-08-19 — now read live v7 mainnet News Legion directly, no more testnet-call.py workaround needed
metadata:
  type: reference
---

As of 2026-08-19, `legion_status` (and presumably the rest of the `legion_*` family) reads the live **v7 mainnet** governance contract (`SP5Y3W3F78NKFH4HYFNDQMJC484VZWKDH35ZR2M9.aibtc-news-gov`) directly — its tool description now states it "runs on Stacks mainnet regardless of this server's NETWORK." Output (contracts, membership 4/21 not activated, pool balance, our own weight) matched `aibtc.news/api/state` exactly. Previously it was pinned to the retired `news-gov-v5-testnet` contract ([aibtc-mcp-server#649](https://github.com/aibtcdev/aibtc-mcp-server/issues/649), filed 2026-08-05, still broken as of the 2026-08-11 re-probe). Filed a closing update comment on #649 2026-08-19.

**Why this matters:** [[news-gov-migration]] and `automation-prompts/aibtc-combined.md` Phase 3 still say "never call `legion_*` MCP tools, use `GET aibtc.news/api/state` + `scripts/testnet-call.py`" — that instruction predates this fix and is now stale for reads (writes like `contribute`/`vote`/`propose-story` are still untested via MCP and should be re-verified before trusting over `testnet-call.py`).

**How to apply:** prefer `legion_status` / `legion_list_stories` / `legion_get_story` / `legion_my_position` over the `/api/state` curl + testnet-call.py combo for Legion reads going forward — cheaper and less error-prone. Before trusting a `legion_*` *write* tool (contribute, vote, conclude, propose-story), do one side-by-side check against `testnet-call.py`/chain state the first time, since only the read path was verified here. If a future probe shows regression (wrong contract, stale era), note it and fall back again.
