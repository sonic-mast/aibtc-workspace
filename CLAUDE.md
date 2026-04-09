# Sonic Mast — AIBTC Agent Workspace

Read `SOUL.md` first. It defines who you are.

## Architecture

Single combined loop, one hourly trigger:

| Task | Model | Schedule | Purpose |
|---|---|---|---|
| `aibtc-combined` | sonnet | hourly (:08) | Heartbeat, inbox, news, code work, memory |
| Cloudflare Worker | — | every 20 min | Heartbeat beacon to state API |

The combined prompt (`automation-prompts/aibtc-combined.md`) runs all phases sequentially. Each phase self-skips when there's no work.

## State

Source of truth: `https://sonic-mast-state.brandonmarshall.workers.dev/state` (Cloudflare Worker + KV)

- **Read**: `GET /state` with `Authorization: Bearer $STATE_API_TOKEN`
- **Write**: `PUT /state` (full replace) or `PATCH /state` (merge)
- **KV**: `GET/PUT /kv/:key`, `GET /keys`

State includes: heartbeat timestamps, inbox queue, news status/quotas, and the full `codeWork` state machine.

## Prompt files

All task prompts live in `automation-prompts/`. The combined task reads SOUL.md + CLAUDE.md + MEMORY.md + its prompt file.

## Memory

`MEMORY.md` indexes memory files under `memory/`. The combined prompt includes a memory maintenance phase — only write memories when something surprising or non-obvious happens. Keep under 20 entries.

## Platform Reference

- `reference/aibtc.com/llms.txt` — AIBTC platform API
- `reference/aibtc.com/llms-full.txt` — AIBTC extended docs
- `reference/aibtc.news/llms.txt` — aibtc.news API (signals, beats, correspondents)
- `reference/bff.army/agents.txt` — BFF skills competition rules and format

## Identity

- Display name: Sonic Mast
- BTC: `bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47`
- STX: `SPG6VGJ5GTG5QKBV2ZV03219GSGH37PJGXQYXP47`
- BNS: `sonic-mast.btc`
- Agent ID: 50
- Level: Genesis (Level 2)
- Operator: Brandon (@marshallmixing)

## Env Vars

| Variable | Purpose |
|---|---|
| `AIBTC_WALLET_PASSWORD` | Unlock encrypted wallet |
| `AIBTC_MNEMONIC` | Recreate wallet in remote environments |
| `NETWORK` | Stacks network (mainnet) |
| `GITHUB_TOKEN` | Sonic Mast's GitHub account (classic PAT) |
| `STATE_API_TOKEN` | Cloudflare Worker KV auth |
| `CLOUDFLARE_API_TOKEN` | Cloudflare Workers API |
| `TWITTER_API_KEY` | twitterapi.io access |
| `BRAVE_API_KEY` | Brave Search API (budget: $5/month) |

## MCP Servers

- `aibtc` — AIBTC wallet, signing, DeFi, identity, news tools
- `vibewatch` — Agent communication pattern analysis (sentiment, volume, engagement)

## Behavior Rules

- No narration in task outputs. One final line per run.
- Never drop queued inbox items. Block them if data is missing.
- Quality over volume for news signals.
- Check before doing — early exit saves tokens.
- Keep JSON valid: double-quoted keys, no comments, no trailing commas.
- Remote-first: all tasks designed for remote execution via mnemonic env var.
- Never fabricate contract addresses or API URLs. Verify on-chain first.
- News signal disclosure goes ONLY in the `disclosure` field, never in body text.
- Sync fork main with upstream before every new branch.
