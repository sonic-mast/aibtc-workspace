---
name: bounty-audit-fix-pr-infeasible
description: Bounty-hunting notes — Zest fix-PR #58 (open, awaiting merge), inference-provider bounty shape, and the source-reading technique that landed a Medium finding on the pillar-safe-v2/jing-mm-safe stress-test bounty
metadata:
  type: project
---

Bounty `mqewgyvr5063fd520a70` ("Fix-PR landing a finding from one of my 5 paid Stacks DeFi audits", 2,000 sats) needs a merged PR on a protocol's official public repo fixing one of 5 named audit findings. Researched 2026-07-06:

**Dead ends (do not re-attempt without new information):**
- **Bitflow CLMM router R02** (`swap-simple-multi` no aggregate output min): function doesn't exist in `BitflowFinance/bitflow-dlmm` main branch at all. The repo's `dlmm-swap-router-v-1-1.clar` (last touched 2025-12-04) is an *older* iteration than the mainnet-deployed contract (verified via Hiro API diff) — repo is out of sync with mainnet, nothing to patch.
- **ALEX AMM v2** (`amm-pool-v2-01` missing blocklist check): only public `alexgo-io` AMM repo is `alex-v1` (stale since 2024-05-23, v1 contracts only). No `alex-v2` repo exists publicly.

**Live and fixable — continue here:**
- **Zest pool-borrow F-01** (`flashloan-liquidation-step-2` solvency guard reads post-loan liquidity instead of pre-loan): confirmed live in `Zest-Protocol/zest-contracts`, file `onchain/contracts/borrow/production/pool/pool-borrow.clar`, lines 548-610. Fix PR opened: https://github.com/Zest-Protocol/zest-contracts/pull/58 ("fix(pool-borrow): snapshot pre-loan liquidity for flashloan-liquidation-step-2 (audit F-01)"), still open as of 2026-07-08 (no maintainer comments/reviews yet, 2 days in). Payout requires `merged: true`, not just an open PR — nothing to do but monitor each run (`bounty_get` + check PR state) until a maintainer acts. Don't re-open a second PR or resubmit; one open PR per finding is enough.

**Unconfirmed** (didn't reach): Granite Finance F-01 and stSTX-STX stableswap F-01 — neither `granite-finance` nor `stacking-dao` GitHub org exists under those names. Only worth chasing if the Zest PR stalls past its 30-day bounty expiry (2026-07-15).

**Why this matters:** contract audits sourced from live on-chain bytecode don't guarantee the finding's target function exists in, or matches, any current public repo — protocols redeploy from private branches or refactor away vulnerable code before a public mirror catches up. Verify the actual file/function is present and current *before* investing in writing a fix.

---

**Separately — inference-provider bounty is a different shape.** `mr33v6w5ff5876a268dd` ("First external inference provider — register + hold 7 days", 10,000 sats, surfaced 2026-07-08, expires 2026-07-23) scores well on reward but isn't a code-PR deliverable — it requires standing up and continuously operating a real GPU/CPU inference endpoint (vLLM/llama.cpp/Ollama/SGLang) for 7 straight days. That's ongoing hosted infra with real compute cost, which the Phase 4.5 scoring guidance's own carve-out says to skip without operator `--confirm` approval, not auto-draft. Leave it off the `bounties` pipeline until Brandon decides whether to host an endpoint; don't re-evaluate it fresh each run.

---

**Contract-audit/stress-test bounties — read live source via Hiro, don't stop at the poster's own bullet list.** On `mrczwu00937221e6b7df` (pillar-safe-v2 + jing-mm-safe passkey smart-wallet stress test, 5,000 sats, drafted+built+submitted same day 2026-07-09), pulled full Clarity source directly — `curl "https://api.hiro.so/extended/v1/contract/{ADDR}.{NAME}"`, source is in the `source_code` field — saved to scratch `.clar` files, grepped `define-public` to map every entrypoint, then read the functions the bounty's threat-model bullets named plus the config/admin functions that gate the security parameters those functions rely on.

Found: `signal-config-change` + `set-wallet-config` are both admin-key-only (no passkey path exists on either function signature) and let `wallet-config.cooldown-period` be set to `u0` with no floor check. After a one-time wait bounded by `min(current cooldown-period, MAX-CONFIG-COOLDOWN=4032 blocks)` (~1 day at the default `u144`), this permanently collapses the propose→cooldown→veto window — the wallet's *entire* defense against a compromised admin key — to zero blocks, with the passkey never involved. The bounty's own explicit bullet list (execute-now guard, rp-id whitelist, transfer escape hatch) didn't name this path; the same stated guarantee ("compromised admin key alone cannot drain over-threshold funds") still applied and broke. Two other submitters on the same bounty (checked via `bounty_get` before submitting) only turned up Low/Informational items or a "no exploit found" writeup — they likely worked from the poster's bullet list rather than the full source. Submission: https://gist.github.com/sonic-mast/b06a08274df7250ed0aba54cb5c61bce

**How to apply:** for any future contract-audit bounty — (1) pull live source via the Hiro contract API before reading any linked audit-gist/README, (2) map every `define-public` entrypoint, (3) don't stop at the bullets the poster lists as the threat model; check whether the same *stated guarantee* holds across every single-factor-reachable path, including config/admin functions that gate a security parameter (cooldown, threshold, whitelist) but don't look like fund-movement functions on their face — those are exactly what defeats a 2FA/timelock guarantee if reachable single-factor with no floor/ceiling check.
