---
name: bounty-audit-fix-pr-infeasible
description: Fix-PR bounty (mqewgyvr5063fd520a70) — Zest F-01 live and fixable (PR #58 open, awaiting maintainer merge); Bitflow/ALEX dead ends. Also covers the inference-provider bounty (needs real hosted infra, not a code-PR); REST fallback host for bounty_get during MCP outage
metadata:
  type: project
---

Bounty `mqewgyvr5063fd520a70` ("Fix-PR landing a finding from one of my 5 paid Stacks DeFi audits", 2,000 sats) needs a merged PR on a protocol's official public repo fixing one of 5 named audit findings. Researched 2026-07-06:

**Dead ends (do not re-attempt without new information):**
- **Bitflow CLMM router R02** (`swap-simple-multi` no aggregate output min): function doesn't exist in `BitflowFinance/bitflow-dlmm` main branch at all. The repo's `dlmm-swap-router-v-1-1.clar` (last touched 2025-12-04) is an *older* iteration than the mainnet-deployed contract (verified via Hiro API diff) — repo is out of sync with mainnet, nothing to patch.
- **ALEX AMM v2** (`amm-pool-v2-01` missing blocklist check): only public `alexgo-io` AMM repo is `alex-v1` (stale since 2024-05-23, v1 contracts only). No `alex-v2` repo exists publicly.

**Live and fixable — continue here:**
- **Zest pool-borrow F-01** (`flashloan-liquidation-step-2` solvency guard reads post-loan liquidity instead of pre-loan): confirmed live in `Zest-Protocol/zest-contracts`, file `onchain/contracts/borrow/production/pool/pool-borrow.clar`, lines 548-610. Fix PR opened: https://github.com/Zest-Protocol/zest-contracts/pull/58 ("fix(pool-borrow): snapshot pre-loan liquidity for flashloan-liquidation-step-2 (audit F-01)"), still open as of 2026-07-08 (no maintainer comments/reviews yet, confirmed unchanged again on 2026-07-08T16:10Z — 2 days in). Payout requires `merged: true`, not just an open PR — nothing to do but monitor each run (`bounty_get` + check PR state) until a maintainer acts. Don't re-open a second PR or resubmit; one open PR per finding is enough.

**Unconfirmed** (didn't reach): Granite Finance F-01 and stSTX-STX stableswap F-01 — neither `granite-finance` nor `stacking-dao` GitHub org exists under those names. Only worth chasing if the Zest PR stalls past its 30-day bounty expiry (2026-07-15).

**Why this matters:** contract audits sourced from live on-chain bytecode don't guarantee the finding's target function exists in, or matches, any current public repo — protocols redeploy from private branches or refactor away vulnerable code before a public mirror catches up. Verify the actual file/function is present and current *before* investing in writing a fix.

---

**Separately — inference-provider bounty is a different shape.** `mr33v6w5ff5876a268dd` ("First external inference provider — register + hold 7 days", 10,000 sats, surfaced 2026-07-08, expires 2026-07-23) scores well on reward but isn't a code-PR deliverable — it requires standing up and continuously operating a real GPU/CPU inference endpoint (vLLM/llama.cpp/Ollama/SGLang) for 7 straight days. That's ongoing hosted infra with real compute cost, which the Phase 4.5 scoring guidance's own carve-out says to skip without operator `--confirm` approval, not auto-draft. Leave it off the `bounties` pipeline until Brandon decides whether to host an endpoint; don't re-evaluate it fresh each run.

---

**2026-07-08 gotcha: `bounty_get`'s REST fallback host, when aibtc MCP tools fail to register.** The Phase 4.5.A guardrail about dropping "dead mq/mqf-prefix" bountyIds (deprecated API — 404s) is about a genuinely stale ID scheme, NOT the normal `mq…`/`mp…`/`mr…` hash-style IDs the platform uses today — those are current and valid. Confirmed live 2026-07-08 with MCP tools unregistered (0 tools, same failure mode as [[cloud-mcp-pattern]]): `curl https://bounty.drx4.xyz/api/bounties/{id}` 404s on a perfectly live, current bounty (`mqewgyvr5063fd520a70`, confirmed open, unpaid, unexpired) — that host only serves its own numeric-id listings and doesn't recognize the platform's hash-style ids at all, host mismatch not a dead bounty. The correct REST fallback for `bounty_get`/`bounty_list` equivalents is **`https://aibtc.com/api/bounties/{id}`** (single) and **`https://aibtc.com/api/bounties?status=open&limit=N`** (list) — both no-auth, no-wallet reads, and return the full platform listing (title, description, rewardSats, expiresAt, submissionCount, status). Don't drop an in-flight bounty on a bounty.drx4.xyz 404 alone; re-check against aibtc.com/api/bounties/{id} first.
