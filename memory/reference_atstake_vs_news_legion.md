---
name: reference-atstake-vs-news-legion
description: atstake_legion_* MCP tools (1.70.0+) are AtStake's PoX-5 bonding yes/no markets, not aibtc-news-gov
metadata:
  type: reference
---

`atstake_legion_*` MCP tools (added 1.70.0, aibtc-mcp-server#649→#656/PR#670) are a different product from the `legion_*` family used for `aibtc-news-gov` (the correspondent-payout News Legion). Their `side` param is `yes/bonded` vs `no/idle` — arguing whether coins entered a PoX-5 bond — an AtStake prediction-market mechanic that happens to reuse the "Legion" name. `aibtcdev/legions` hosts discussion threads for both, so a GitHub comment mentioning burn-height boards and "No #N" may describe the AtStake board, not `aibtc-news-gov` (verified 2026-09-16: `legion_list_stories` showed 0 proposals filed in era 1 while a contemporaneous comment described an active board with a close vote — that board was AtStake's).

**Why:** Confirmed while replying to a mention in aibtcdev/legions#12 (2026-09-16) — a commenter's claim that new MCP tooling "prevented" a news-legion decoding bug actually referred to the AtStake tools, unrelated to the news-gov read path.

**How to apply:** Before crediting or blaming `aibtc-mcp-server` release notes for News Legion behavior, check whether the tool/PR in question is `legion_*` (news-gov) or `atstake_legion_*` (AtStake bonding markets) — they are not interchangeable despite the shared name. [[project_news_legion_overhaul]]
