# Sonic Mast — AIBTC Agent Workspace

Read `SOUL.md` first. It defines who you are.

## Architecture

Scanner/worker split optimized for token usage:

| Task | Model | Schedule | Purpose |
|---|---|---|---|
| `aibtc-pulse` | haiku | every 20 min | Heartbeat + inbox scan + news quota check |
| `aibtc-reply-worker` | sonnet | every 30 min | Compose + send inbox replies (self-skips if empty) |
| `aibtc-news-correspondent` | sonnet | hourly | Research + file signals (self-skips if not eligible) |
| `refresh-reference` | haiku | daily 8:17 AM | Refresh llms.txt reference files |

Pulse gates everything. Workers self-skip when no work is flagged.

## State

Source of truth: `https://sonic-mast-state.brandonmarshall.workers.dev/state` (Cloudflare Worker + KV)

Pulse writes `unreadCount`, `pendingReplyIds`, `newsEligible`. Workers read these.

Local backup: `automation-state/aibtc-core.json` (may be stale — the API is canonical).

## Prompt files

All task prompts live in `automation-prompts/`. Each scheduled task reads SOUL.md + its prompt file.

## Platform Reference

- `reference/aibtc.com/llms.txt` — AIBTC platform API
- `reference/aibtc.com/llms-full.txt` — AIBTC extended docs
- `reference/aibtc.news/llms.txt` — aibtc.news API (signals, beats, correspondents)
- `reference/bff.army/agents.txt` — BFF skills competition (future use)

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
| `GITHUB_TOKEN` | Shelly's GitHub account (classic PAT) |
| `CLOUDFLARE_API_TOKEN` | Cloudflare Workers API |
| `TWITTER_API_KEY` | twitterapi.io access |
| `BRAVE_API_KEY` | Brave Search API (budget: $5/month) |

## MCP Servers

- `aibtc` — AIBTC wallet, signing, DeFi, identity, news tools (pinned @1.46.3)
- `vibewatch` — Agent communication pattern analysis (sentiment, volume, engagement)

## Behavior Rules

- No narration in task outputs. One final line per run.
- Never drop queued inbox items. Block them if data is missing.
- Quality over volume for news signals.
- Check before doing — early exit saves tokens.
- Keep JSON valid: double-quoted keys, no comments, no trailing commas.
- Remote-first: all tasks designed for remote execution via mnemonic env var.
