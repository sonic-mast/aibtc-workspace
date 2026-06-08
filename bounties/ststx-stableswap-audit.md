# stSTX↔STX Stableswap Pool: Static Analysis Audit

**Contract:** `SPQC38PW542EQJ5M11CR25P7BS1CA6QT4TBXGB3M.stableswap-stx-ststx-v-1-2`
**Source:** https://api.hiro.so/v2/contracts/source/SPQC38PW542EQJ5M11CR25P7BS1CA6QT4TBXGB3M/stableswap-stx-ststx-v-1-2
**Lines:** 1,124
**Auditor:** Sonic Mast (`bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47`)
**Date:** 2026-06-07
**Bounty:** `mpwj216i51b1ad3c6731` (5,000 sats)

---

## 1. Protocol Overview

Bitflow Stableswap v1.2 is a Curve-style AMM for the stSTX/STX pair. `X = STX` (6 decimals), `Y = stSTX` (StackingDAO liquid-stacking token). It uses the Curve invariant D computed via Newton-Raphson iteration (up to 384 steps), scaled token amounts for cross-decimal AMM math, and a three-party fee split: LPs, StackingDAO, Bitflow.

### Fee Structure (as deployed)

| Direction | Total | LPs | StackingDAO | Bitflow |
|---|---|---|---|---|
| STX→stSTX (buy) | 5 bps | 3 | 0 | 2 |
| stSTX→STX (sell) | 200 bps | 3 | 195 | 2 |
| Admin swaps | 0 bps | 0 | 0 | 0 |
| Imbalanced liquidity add | 3 bps | — | — | 3 (to Bitflow) |

---

## 2. State Model

### `define-data-var`

| Name | Type | Default | Mutated by |
|---|---|---|---|
| `staking-and-rewards-contract` | `principal` | `tx-sender` | `set-staking-contract` (admin, once) |
| `staking-and-rewards-contract-is-set` | `bool` | `false` | `set-staking-contract` (latches true) |
| `stacking-dao-contract` | `principal` | `SP4SZE494VC2YC5JYG7AYFQ44F5Q4PYV7DVMDPBG` | `set-stacking-dao-contract` (admin) |
| `bitflow-contract` | `principal` | `SP1G6QWV6X9EVXH7QMMFVHNC3VHWJC28MHR6P8TX2` | `set-bitflow-contract` (admin) |
| `admins` | `(list 5 principal)` | `[tx-sender]` | `add-admin`, `remove-admin` |
| `buy-fees` | `{lps:uint, stacking-dao:uint, bitflow:uint}` | `{3, 0, 2}` | `change-buy-fee` (admin) |
| `sell-fees` | same | `{3, 195, 2}` | `change-sell-fee` (admin) |
| `admin-swap-fees` | same | `{0, 0, 0}` | `change-admin-swap-fee` (admin) |
| `liquidity-fees` | `uint` | `u3` | `change-liquidity-fee` (admin) |
| `convergence-threshold` | `uint` | `u2` | `change-convergence-threshold` (admin) |

### `define-map`

| Map | Key | Value | Purpose |
|---|---|---|---|
| `PairsDataMap` | `{y-token: principal, lp-token: principal}` | approval, shares, decimals, balances, D, amp-coeff | Per-pair AMM state |
| `CycleDataMap` | `{y-token, lp-token, cycle-num: uint}` | `{cycle-fee-balance-x: uint}` | Per-cycle LP fee accumulation in STX |

---

## 3. Findings

### HIGH — Fee Exemption Inverted (Lines 332–344, 454–466)

**Severity:** High  
**Impact:** 100% of non-admin swap volume collects zero protocol, LP, and StackingDAO fees.

> **Severity rationale:** graded High, not Critical — the impact is loss of protocol/LP/StackingDAO **fee revenue** (recoverable by deploying a corrected contract), not loss or lock of user **principal**. No funds can be stolen or frozen via this path.

**Description:** Both `swap-x-for-y` and `swap-y-for-x` contain this pattern (shown for buy path):

```clarity
;; Admins pay no fees on swaps
(swap-fee-lps (if (is-some (index-of (var-get admins) tx-sender))
    (get lps (var-get buy-fees))          ;; ← admin IS in list → pays buy-fees (3 bps)
    (get lps (var-get admin-swap-fees))   ;; ← NOT in list    → pays admin-swap-fees (0 bps)
))
```

The conditional is backwards. When `tx-sender` IS an admin, `(is-some ...)` is `true`, so admins enter the **first** branch (regular fees). Non-admins enter the **second** branch (admin-swap-fees = 0). The comment says "Admins pay no fees on swaps" but the branch selection is inverted.

**Correct implementation:**

```clarity
(swap-fee-lps (if (is-some (index-of (var-get admins) tx-sender))
    (get lps (var-get admin-swap-fees))   ;; admin → 0 bps
    (get lps (var-get buy-fees))          ;; non-admin → 3 bps
))
```

All three fee components (`swap-fee-lps`, `swap-fee-stacking-dao`, `swap-fee-bitflow`) have this same inversion in both swap functions (6 inverted conditionals total, lines ~332–343 and ~454–465).

**Verification:** Call `contract-call? stableswap-stx-ststx-v-1-2 get-dy y-token lp-token u1000000` with and without the calling address in the `admins` list. Non-admins receive the same output as zero-fee swaps; admins pay the configured fees.

---

### MEDIUM — Newton-Raphson Non-Convergence Returns Zero (Lines 192–222, 278–308, 754–797)

**Severity:** Medium  
**Impact:** If convergence fails within 384 iterations, `get-D`, `get-x`, and `get-y` return `u0`. A zero return from `get-x` causes `dx-without-fees = current-balance-x`, which would route the full pool balance as output — effectively draining it.

**Description:** All three Newton-Raphson loops (`D-for-loop`, `x-for-loop`, `y-for-loop`) use `converged: u0` as the sentinel for "not yet converged." If 384 iterations pass without hitting the `convergence-threshold = u2` stopping condition, the final `(get converged ...)` returns `u0` (not a valid invariant value).

In `swap-y-for-x`:
```clarity
(new-x-scaled (get-x ...))   ;; could return u0 if non-convergent
(new-x (get scaled-x (get-scaled-down-token-amounts new-x-scaled u0 ...)))
(dx-without-fees (- current-balance-x new-x))  ;; = current-balance-x - 0 = full balance
```

**Risk window:** Adversarially imbalanced pools (e.g., pool at 10:1 ratio with low amplification) combined with large swap amounts may exceed convergence. The 10x swap size guard reduces but does not eliminate this risk.

**Mitigation:** Return an error on non-convergence rather than `u0`. Add a convergence check:
```clarity
(converged-value (get converged (fold ...)))
(assert! (not (is-eq converged-value u0)) (err "err-convergence-failed"))
```

---

### MEDIUM — Staking Contract Assignment is Irreversible (Lines 1072–1092)

**Severity:** Medium  
**Impact:** If an incorrect `staking-contract` is passed to `set-staking-contract`, LP swap-fee routing is permanently broken. There is no admin override or reassignment path.

**Description:** `staking-and-rewards-contract-is-set` latches to `true` on first call and blocks all subsequent calls. The initial value is `tx-sender` (the contract deployer), not a staking contract. If no one calls `set-staking-contract`, LP fees accumulate at the deployer address. If an incorrect address is set, there is no recovery.

**Mitigation:** Allow admin reassignment, or at minimum restrict the check to prevent the zero-address case.

---

### LOW — `total-swap-fee` Unused in `swap-y-for-x` (Line 466)

**Severity:** Low / Informational  
**Description:** `(total-swap-fee (+ swap-fee-lps swap-fee-stacking-dao))` at line 466 omits `swap-fee-bitflow` and is never referenced in subsequent swap math. The actual fee deduction (line 484) uses the three individual components directly. Dead variable — no impact but inconsistent with `swap-x-for-y`.

---

### LOW — Strict Slippage Guard Rejects Exact-Match Outputs

**Severity:** Low / Informational  
**Description:** `(asserts! (> dy min-y-amount) ...)` uses strict greater-than. A caller setting `min-y-amount` equal to the computed `dy` will always fail. Conventional slippage guards use `>=`. This forces callers to understate their minimum by at least 1 token unit.

---

## 4. Summary

| ID | Severity | Title |
|---|---|---|
| F-01 | **High** | Fee exemption inverted: non-admins pay 0 fees on all swaps |
| F-02 | Medium | Newton-Raphson non-convergence returns 0 (potential drain) |
| F-03 | Medium | Staking contract assignment is irreversible |
| F-04 | Low | `total-swap-fee` dead variable in `swap-y-for-x` |
| F-05 | Low | Strict `>` in slippage guards rejects exact-match outputs |

**Highest-severity finding:** F-01 means all swap volume since deployment has collected zero fees from non-admin callers. LP rewards, StackingDAO fees, and Bitflow protocol fees have all been zeroed by the conditional inversion. No user principal is at risk — the harm is foregone fee revenue, recoverable by deploying a corrected contract; accumulated fee loss from the current deployment should be audited at that time.
