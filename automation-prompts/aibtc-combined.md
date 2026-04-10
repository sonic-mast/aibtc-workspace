# AIBTC Combined Task

Runs on Sonnet on-demand. Executes Pulse → Reply Worker → News Correspondent in a single session.

Read `SOUL.md` for identity and voice.

## State API

- **Read**: `curl -s https://sonic-mast-state.brandonmarshall.workers.dev/state -H "Authorization: Bearer $STATE_API_TOKEN"`
- **Patch**: `curl -s -X PATCH https://sonic-mast-state.brandonmarshall.workers.dev/state -H "Authorization: Bearer $STATE_API_TOKEN" -H "Content-Type: application/json" -d '{...}'`
- **Put**: `curl -s -X PUT https://sonic-mast-state.brandonmarshall.workers.dev/state -H "Authorization: Bearer $STATE_API_TOKEN" -H "Content-Type: application/json" -d '{...}'`

Read `STATE_API_TOKEN` from the environment.

## Execution Order

Run each phase in sequence. Each phase may self-skip based on state.

---

## Phase 1: Pulse

Follow `automation-prompts/aibtc-pulse.md` exactly:

1. Read state.
2. Unlock wallet (use `AIBTC_WALLET_PASSWORD` env var).
3. Heartbeat: sign `AIBTC Check-In | {timestamp}`, POST to `https://aibtc.com/api/heartbeat`.
4. Inbox scan: only if `unreadCount > 0` and `pendingReplyIds` is empty. Queue at most 3 unread items.
5. News quota check: only if `newsLastQuotaCheck` is null or >15 min stale. Fetch `https://aibtc.news/api/status/bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47` and update `newsEligible`.
6. PUT updated state.

---

## Phase 2: Reply Worker

Follow `automation-prompts/aibtc-reply-worker.md` exactly:

**Self-skip** if `pendingReplyIds` is empty after Pulse.

Otherwise:
1. Build `actionableReplyIds` (exclude `blocked_missing_sender_btc`).
2. Process at most 2 items: fetch full message, compose reply in Sonic Mast's voice, sign and POST to outbox (or mark read if informational).
3. Only clear items from state after successful action.
4. PUT updated state.

---

## Phase 3: News Correspondent

Follow `automation-prompts/aibtc-news-correspondent.md` exactly:

**Self-skip** if `newsEligible` is not `true` after Pulse.

Otherwise:
1. Verify eligibility via `https://aibtc.news/api/status/bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47`.
2. Choose beat (rotate — check recent signals to avoid repeating).
3. Dedup check: fetch last 15 signals.
4. Research (2-3 sources max, frugal with Brave Search budget).
5. Dedup filter: skip if same headline/topic/beat within 3 hours.
6. File signal via BIP-322 auth POST to `https://aibtc.news/api/signals`.
7. PATCH state: `newsEligible = false`, increment `newsSignalsToday`.

---

## Finalize

PUT final state with updated `lastRunSummary`.

Final response: exactly one plain-text line:

`AIBTC Combined | ok | heartbeat={checkInCount} | level={levelName} | unread={unreadCount} | replied={handledCount} | news={beat:slug|skip:reason}`

## Rules

- No markdown, no bullets, no code fences in final response.
- On any hard failure: PATCH state with error in `lastRunSummary`, end with:
  `AIBTC Combined | error | {short concrete reason}`
- Keep JSON valid: double-quoted keys, no comments, no trailing commas.
- Never expose wallet mnemonics, API keys, or operator details in outputs.
