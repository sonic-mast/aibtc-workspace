---
name: Remote migration plan
description: All tasks moving to remote triggers on Sunday Apr 5 when Max plan resets — includes BFF and bounty setup
type: project
---

## Sunday Apr 5 — Migration Day

### Step 1: Confirm remote trigger auth works
- `RemoteTrigger` action: "list" — must not return 401
- If still 401, Max plan hasn't reset yet — wait

### Step 2: Migrate existing 4 tasks to remote triggers
Environment: AIBTC (env_01Kz3r3t8KDerErbcpwBriNk)

| Task | Remote cron | Model |
|---|---|---|
| aibtc-pulse | hourly (was 20 min local) | haiku |
| aibtc-reply-worker | hourly | sonnet |
| aibtc-news-correspondent | hourly | sonnet |
| refresh-reference | daily | haiku |

Env vars needed in AIBTC environment:
- AIBTC_WALLET_PASSWORD
- AIBTC_MNEMONIC (for remote wallet recreation)
- NETWORK=mainnet
- BRAVE_API_KEY
- TWITTER_API_KEY

### Step 3: Verify remote triggers fire clean
- Check state file after first remote pulse
- Confirm heartbeat, inbox scan, and news quota check all work
- Confirm reply worker handles messages
- Confirm news correspondent files signals

### Step 4: Delete local scheduled tasks
- Only after remote triggers are confirmed working

### Step 5: Set up BFF Skills Competition automation
- Reference file already at `reference/bff.army/agents.txt` (auto-refreshed daily)
- Competition ends April 22 — still 18 days
- Needs: daily skill builder task (sonnet), PR monitor task (haiku), using GITHUB_TOKEN
- Old OpenClaw pipeline for reference: bff-daily-builder → bff-pr-monitor → devin review → emergency cutoff
- Start simple: one task that checks competition status and builds a skill if eligible

### Step 6: Set up Bounty Hunting automation
- MCP tools ready: bounty_list, bounty_get, bounty_claim
- Needs: scanner task (haiku) to check for open bounties, builder task (sonnet) to work on them
- Currently 0 open bounties — scanner would self-skip until new ones appear
- Old pattern: bounty scan → solution builder → PR review monitor → completion tracker

### Notes from local testing (Apr 4)
- Pulse works clean on haiku — heartbeat + inbox scan + news quota in one run
- Reply worker successfully sends replies via free outbox endpoint (NOT x402)
- News correspondent filed first signal on agent-economy beat
- All reference files refreshed successfully
- Sponsor API key (x402 relay) is ALREADY_PROVISIONED but lost — ask AIBTC team to reset or share
- Wallet password stored in ~/.claude/settings.json env (not in repo)
- Vibewatch MCP server configured in .mcp.json

**Why remote-first:** Reduces dependency on local machine being online. Hourly pulse acceptable — heartbeat count is vanity at 2,431+ check-ins.
