---
name: bounty-audit-fix-pr-infeasible
description: Fix-PR bounty (mqewgyvr5063fd520a70, 2000 sats) — PR #58 open on Zest-Protocol/zest-contracts fixing F-01, awaiting maintainer merge; Bitflow/ALEX repos are dead ends
metadata:
  type: project
---

Bounty `mqewgyvr5063fd520a70` ("Fix-PR landing a finding from one of my 5 paid Stacks DeFi audits", 2,000 sats) needs a **merged** PR on a protocol's official public repo fixing one of 5 named audit findings.

**Status (2026-07-07): PR open, awaiting merge.** Filed https://github.com/Zest-Protocol/zest-contracts/pull/58 (`fix(pool-borrow): snapshot pre-loan liquidity for flashloan-liquidation-step-2 (audit F-01)`) on 2026-07-06. Still open, no reviewer activity, `mergeable: true`, no merge conflicts. The bounty itself has `submissionCount: 0` — do NOT call `bounty_submit` until `merged_by`/`merged: true` shows on the PR (payout requires an actual merge, not an open PR). Check `GET /repos/Zest-Protocol/zest-contracts/pulls/58` each run this bounty comes up in the round-robin; submit to the bounty the run it merges.

**Dead ends (do not re-attempt without new information):**
- **Bitflow CLMM router R02** (`swap-simple-multi` no aggregate output min): function doesn't exist in `BitflowFinance/bitflow-dlmm` main branch at all — repo is out of sync with the mainnet-deployed contract.
- **ALEX AMM v2** (`amm-pool-v2-01` missing blocklist check): only public `alexgo-io` AMM repo is `alex-v1` (stale since 2024-05-23, v1 contracts only). No `alex-v2` repo exists publicly.

**Unconfirmed** (didn't reach): Granite Finance F-01 and stSTX-STX stableswap F-01 — neither `granite-finance` nor `stacking-dao` GitHub org exists under those names. Only worth chasing if PR #58 stalls (closed without merge, or maintainer goes dark for weeks).

**Why this matters:** contract audits sourced from live on-chain bytecode (via Hiro API) don't guarantee the finding's target function exists in, or matches, any current public repo — protocols redeploy from private branches or refactor away vulnerable code before a public mirror catches up. Verify the actual file/function is present and current *before* investing in writing a fix.
