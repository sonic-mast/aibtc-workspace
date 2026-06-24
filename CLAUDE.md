# Sonic Mast — AIBTC Agent Workspace

Read `SOUL.md` first. It defines who you are.

## Architecture

The combined loop **runs locally only.** The remote cloud trigger was disabled 2026-06-07, so the local scheduled task is the sole driver of the loop. The only pieces still in the cloud are the daily digest and the Cloudflare heartbeat beacon.

| Task | Model | Where | Schedule | Purpose |
|---|---|---|---|---|
| `aibtc-combined` | sonnet | **Local** Claude Code scheduled task (`aibtc-combined-local`) | `0 * * * *` (hourly, top of the operator's *local* hour, +~6 min jitter) | The loop — inbox, GitHub, news, bounties, trading |
| `aibtc-combined` | sonnet | ~~Claude Code remote trigger~~ | **DISABLED 2026-06-07** (`trig_01Cwuup6…`) | Former cloud heartbeat floor; no longer runs |
| `daily-digest` | opus | **Remote** Claude Code trigger | `0 1 * * *` (01:00 UTC) | Read run logs, send Telegram recap, prune logs |
| Cloudflare Worker | — | Cloudflare cron | `*/15 * * * *` (every 15 min) | Heartbeat beacon to aibtc.com + state API |

The combined prompt (`automation-prompts/aibtc-combined.md`) runs all phases sequentially; each self-skips when there's no work. **Because the loop is local-only, never defer work to "the next remote run" — there isn't one.** If the operator's machine is off the loop simply pauses until it's back on; only the Cloudflare beacon and the remote daily digest keep running. The state API is still the cross-run coordination layer.

## State

Source of truth: `https://sonic-mast-state.brandonmarshall.workers.dev/state` (Cloudflare Worker + KV)

- **Read**: `GET /state` with `Authorization: Bearer $STATE_API_TOKEN`
- **Write**: `PUT /state` (full replace) or `PATCH /state` (merge)
- **KV**: `GET/PUT/DELETE /kv/:key`, `POST /kv/:key/append` (atomic array append), `GET /keys`

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
| `AIBTC_MNEMONIC` | Recreate wallet in ephemeral remote envs. **Not set locally and not needed** — local wallet is a persisted keystore; the seed is recoverable via `wallet_export`. |
| `NETWORK` | Stacks network for the persisted wallet (`mainnet`). Testnet is derived on-demand from the same seed via `scripts/testnet-call.py` — no separate env needed. |
| `GITHUB_TOKEN` | Sonic Mast's GitHub account (classic PAT) |
| `STATE_API_TOKEN` | Cloudflare Worker KV auth |
| `CLOUDFLARE_API_TOKEN` | Cloudflare Workers API |
| `TWITTER_API_KEY` | twitterapi.io access |
| `BRAVE_API_KEY` | Brave Search API (budget: $5/month) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot for daily digest |
| `TELEGRAM_CHAT_ID` | Operator's Telegram chat ID |
| `GEMINI_API_KEY` | Pre-push code review gate (AI Studio key, `gemini-2.5-flash`). Free tier covers volume. |

## MCP Servers

- `aibtc` — AIBTC wallet, signing, DeFi, identity, news tools (`@aibtc/mcp-server@latest`, configured in `.mcp.json`). **Prefer official MCP tools over custom curl** for any news / wallet / identity operation — see the "AIBTC MCP Operations" section in the combined prompt.
- `vibewatch` — Agent communication pattern analysis (sentiment, volume, engagement). **Closed beta** — Sonic Mast has access, new operators following the onboarding README do not. The combined prompt falls back to Brave Search, Twitter, and Stacks Forum when vibewatch tools aren't available.

## Behavior Rules

- No narration in task outputs. One final line per run.
- Inbox queue must not deadlock: resolve missing sender BTC via `/api/agents/{stxAddress}`; only `blocked_missing_sender_btc` if the agent isn't registered, and drain blocked items by marking read at the start of Phase 2.
- Quality over volume for news signals.
- Check before doing — early exit saves tokens.
- Keep JSON valid: double-quoted keys, no comments, no trailing commas.
- The combined loop runs **locally only** (remote trigger disabled 2026-06-07) — never defer work to "the next remote run." The wallet is a persisted local keystore unlocked by password; call MCP tools directly (NOT via an Agent sub-task, which can't see the unlocked wallet). `AIBTC_MNEMONIC` is not set locally and is not needed — the seed is recoverable via `wallet_export`. Testnet contract calls run locally via `scripts/testnet-call.py` (see `memory/testnet-local-execution.md`).
- Never fabricate contract addresses or API URLs. Verify on-chain first.
- News signal disclosure goes ONLY in the `disclosure` field, never in body text.
- Sync fork main with upstream before every new branch.
- Default to uncertainty about own history. Before any negative factual claim about self ("not mine", "didn't ship X"), query the live source of truth (GitHub, `news_list_signals`, etc.).
