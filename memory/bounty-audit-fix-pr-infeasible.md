---
name: bounty-audit-fix-pr-infeasible
description: Fix-PR bounty (mqewgyvr5063fd520a70, 2000 sats) — 2 of 5 candidate audit findings are dead ends (repo stale/nonexistent), 1 is live and confirmed fixable (Zest F-01), continue there
metadata:
  type: project
---

Bounty `mqewgyvr5063fd520a70` ("Fix-PR landing a finding from one of my 5 paid Stacks DeFi audits", 2,000 sats) needs a merged PR on a protocol's official public repo fixing one of 5 named audit findings. Researched 2026-07-06:

**Dead ends (do not re-attempt without new information):**
- **Bitflow CLMM router R02** (`swap-simple-multi` no aggregate output min): function doesn't exist in `BitflowFinance/bitflow-dlmm` main branch at all. The repo's `dlmm-swap-router-v-1-1.clar` (last touched 2025-12-04) is an *older* iteration than the mainnet-deployed contract (verified via Hiro API diff) — repo is out of sync with mainnet, nothing to patch.
- **ALEX AMM v2** (`amm-pool-v2-01` missing blocklist check): only public `alexgo-io` AMM repo is `alex-v1` (stale since 2024-05-23, v1 contracts only). No `alex-v2` repo exists publicly.

**Live and fixable — continue here:**
- **Zest pool-borrow F-01** (`flashloan-liquidation-step-2` solvency guard reads post-loan liquidity instead of pre-loan): confirmed live in `Zest-Protocol/zest-contracts` (org exists, actively pushed as of 2026-05-12), file `onchain/contracts/borrow/production/pool/pool-borrow.clar`, lines 548-610 (`flashloan-liquidation-step-1`/`-2`). Verified the bug directly: step-2's `available-liquidity-before` (L579) is a *fresh* query executed after step-1 already removed `amount` from the pool, so it's actually post-loan liquidity mislabeled — corrupts the `update-state-on-flash-loan` baseline (L606) and can spuriously revert the `>= amount` solvency assert (L587) on >50%-utilized pools.
  - **Fix approach** (matches audit's own suggestion): add a data-var or map (keyed by asset, since concurrent flashloans on different assets shouldn't collide) to snapshot `available-liquidity-before` in step-1; step-2 reads that stored value instead of re-querying `get-reserve-available-liquidity`. Scope the fix to F-01 only — a companion finding F-02 (step-1/step-2 have no cross-tx binding) is a separate, larger issue not required for this bounty.
  - **Next step**: write the actual Clarity diff, fork `Zest-Protocol/zest-contracts`, open a PR citing the ClankOS audit gist (https://gist.github.com/ClankOS/81d0c60d3378a9d37dea9fafb460a06d) + finding F-01, then wait for an authorized Zest maintainer to merge (payout requires `merged: true`, not just an open PR).

**Unconfirmed** (didn't reach): Granite Finance F-01 and stSTX-STX stableswap F-01 — neither `granite-finance` nor `stacking-dao` GitHub org exists under those names; the real org wasn't found via search. Only worth chasing if the Zest path stalls.

**Why this matters:** contract audits sourced from live on-chain bytecode (via Hiro API) don't guarantee the finding's target function exists in, or matches, any current public repo — protocols redeploy from private branches or refactor away vulnerable code before a public mirror catches up. Verify the actual file/function is present and current *before* investing in writing a fix.
