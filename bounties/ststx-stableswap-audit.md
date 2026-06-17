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

---

## 5. Function Inventory

### `define-public` (17 functions)

| Function | Caller | Parameters | Effect |
|---|---|---|---|
| `swap-x-for-y` | open | `y-token lp-token x-amount min-y-amount` | STX→stSTX swap; pair approval required; 10× size guard |
| `swap-y-for-x` | open | `y-token lp-token y-amount min-x-amount` | stSTX→STX swap; pair approval required; 10× size guard |
| `add-liquidity` | open | `y-token lp-token x-amount-added y-amount-added min-lp-amount` | Deposits X+Y, mints LP; pair approval required |
| `withdraw-liquidity` | open | `y-token lp-token lp-amount min-x-amount min-y-amount` | Burns LP, returns X+Y; **no approval check** |
| `create-pair` | admin | `y-token lp-token x-decimals y-decimals initial-x initial-y` | Initializes `PairsDataMap`, deposits seed liquidity |
| `set-pair-approval` | admin | `y-token lp-token approval` | Toggles pair approved flag |
| `add-admin` | admin | `new-admin` | Appends to admins list; fails at capacity (5); **no duplicate check** |
| `remove-admin` | admin | `remove` | Filters admins list; deployer address is protected |
| `change-buy-fee` | admin | `new-lps new-stacking-dao new-bitflow` | Replaces `buy-fees`; **no upper bound** |
| `change-sell-fee` | admin | `new-lps new-stacking-dao new-bitflow` | Replaces `sell-fees`; **no upper bound** |
| `change-admin-swap-fee` | admin | `new-lps new-stacking-dao new-bitflow` | Replaces `admin-swap-fees`; **no upper bound** |
| `change-liquidity-fee` | admin | `new-fee` | Replaces `liquidity-fees`; **no upper bound** |
| `change-amplification-coefficient` | admin | `y-token lp-token new-amp` | Instant amp change; **no ramp, no timelock** |
| `change-convergence-threshold` | admin | `new-threshold` | Replaces `convergence-threshold`; accepts `u0` |
| `set-staking-contract` | admin, once | `staking-contract` | Sets LP fee recipient; **irreversible latch** (F-03) |
| `set-stacking-dao-contract` | admin | `addr` | Replaces `stacking-dao-contract`; reassignable |
| `set-bitflow-contract` | admin | `addr` | Replaces `bitflow-contract`; reassignable |

### `define-read-only` (selected)

| Function | Purpose | Convergence risk |
|---|---|---|
| `get-dx(y-token, lp-token, y-amount)` | Quote stSTX→STX output amount | Via `get-x` |
| `get-dy(y-token, lp-token, x-amount)` | Quote STX→stSTX output amount | Via `get-y` |
| `get-x(y-bal, x-bal, y-amount, ann)` | Newton-Raphson solve for pool X after swap | Returns `u0` if not converged (F-02) |
| `get-y(x-bal, y-bal, x-amount, ann)` | Newton-Raphson solve for pool Y after swap | Returns `u0` if not converged (F-02) |
| `get-D(x-bal, y-bal, ann)` | Compute Curve invariant D | Returns `u0` if not converged (F-02) |
| `get-pair-data(y-token, lp-token)` | Read `PairsDataMap` entry | — |
| `get-cycle-data(y-token, lp-token, cycle-num)` | Read `CycleDataMap` entry | — |
| `get-cycle-from-height(height)` | Compute cycle number from block height | — |
| `get-scaled-up-token-amounts(x, y, x-dec, y-dec)` | Scale balances to common precision for AMM math | — |
| `get-scaled-down-token-amounts(x-s, y-s, x-dec, y-dec)` | Scale back to native token precision | — |
| `get-admins()` / `get-buy-fees()` / etc. | Read state vars | — |

---

## 6. Post-condition Coverage Matrix

In Clarity, post-conditions are set by the **caller**, not enforced within contract code. The table below maps each public function's asset flows so callers can construct correct post-conditions.

| Function | STX Out (from caller) | STX In (to caller) | stSTX Out | stSTX In | LP Minted | LP Burned |
|---|---|---|---|---|---|---|
| `swap-x-for-y` | `x-amount` (split: contract + staking + stacking-dao + bitflow) | 0 | 0 | `dy` (from contract) | 0 | 0 |
| `swap-y-for-x` | 0 | `dx` (from contract) | `y-amount` (split: contract + stacking-dao) | 0 | 0 | 0 |
| `add-liquidity` | `x-amount-added` | 0 | `y-amount-added` | 0 | ✓ | 0 |
| `withdraw-liquidity` | 0 | `x-amount` | 0 | `y-amount` | 0 | ✓ |
| `create-pair` | `initial-x` | 0 | `initial-y` | 0 | ✓ (seed) | 0 |

**Note on F-01 impact:** Because the fee conditional is inverted, non-admin callers are routed through `admin-swap-fees = {0, 0, 0}`. The `if (> fee u0) (transfer ...) false` guards skip all three fee transfers when fee = 0. This means non-admin swap calls currently only produce **two** STX movements (caller → contract for net amount; contract → caller for stSTX), not four. Any post-condition suite built against the deployed contract will break after the fee inversion is fixed.

---

## 7. Authority / Access-Control Matrix

### Admin check pattern (all 13 admin-gated functions)

```clarity
(asserts! (is-some (index-of (var-get admins) tx-sender)) (err "err-not-admin"))
```

The `admins` list is a `(list 5 principal)` initialized with `tx-sender` at deployment. Maximum 5 admins; the list cannot grow beyond 5.

### Deployer protection in `remove-admin`

```clarity
(asserts! (not (is-eq remove deployer-address)) (err "err-cannot-remove-deployer"))
```

`deployer-address` is a `define-constant` set at deploy time — immutable. The deployer principal can never be removed from the admin list.

### Matrix

| Function | Open | Admin | Once-only | Deployer-protected | Additional guard |
|---|---|---|---|---|---|
| `swap-x-for-y` | ✓ | — | — | — | `current-approval`, `x-amount < 10× balance-x` |
| `swap-y-for-x` | ✓ | — | — | — | `current-approval`, `y-amount < 10× balance-y` |
| `add-liquidity` | ✓ | — | — | — | `current-approval` |
| `withdraw-liquidity` | ✓ | — | — | — | *(none — no approval check)* |
| `create-pair` | — | ✓ | — | — | — |
| `set-pair-approval` | — | ✓ | — | — | — |
| `add-admin` | — | ✓ | — | — | List capacity check (≤ 5) |
| `remove-admin` | — | ✓ | — | ✓ | Cannot remove deployer |
| `change-buy-fee` | — | ✓ | — | — | No bounds |
| `change-sell-fee` | — | ✓ | — | — | No bounds |
| `change-admin-swap-fee` | — | ✓ | — | — | No bounds |
| `change-liquidity-fee` | — | ✓ | — | — | No bounds |
| `change-amplification-coefficient` | — | ✓ | — | — | No ramp/timelock |
| `change-convergence-threshold` | — | ✓ | — | — | Accepts `u0` |
| `set-staking-contract` | — | ✓ | ✓ | — | Latch: `staking-and-rewards-contract-is-set` |
| `set-stacking-dao-contract` | — | ✓ | — | — | — |
| `set-bitflow-contract` | — | ✓ | — | — | — |

---

## 8. Clarity Best-Practice Review

### BP-01 — No upper bounds on fee parameters

`change-buy-fee`, `change-sell-fee`, `change-admin-swap-fee`, and `change-liquidity-fee` accept any `uint` value. An admin could set any fee component to `u10000` (100%) or higher, making swaps produce zero or negative output after integer division truncation. Recommend capping at a protocol-defined maximum (e.g., `u500` for any single component, `u1000` total).

### BP-02 — Amplification coefficient changeable without ramp

`change-amplification-coefficient` takes effect in the same block it is called. The reference Curve implementation requires a minimum 7-day linear ramp (`A_PRECISION`-scaled) to prevent governance sandwich attacks: a large swap can be sandwiched around an instant amp reduction to extract LP value. Recommend a per-pair `amp-ramp-start` / `amp-ramp-end` / `amp-ramp-start-time` / `amp-ramp-stop-time` mechanism.

### BP-03 — Newton-Raphson sentinel `u0` is ambiguous

All three fold-based loops use `converged: u0` as the "not yet converged" sentinel, but `u0` is also a mathematically possible return for degenerate inputs (zero balance). The caller cannot distinguish "converged to zero" from "never converged." This is the root of F-02. A separate boolean flag (`is-converged`) or a dedicated error return would be unambiguous.

### BP-04 — `withdraw-liquidity` lacks approval guard

`swap-x-for-y`, `swap-y-for-x`, and `add-liquidity` all check `(asserts! current-approval ...)` before proceeding. `withdraw-liquidity` does not. This asymmetry means users can always exit a paused pair — which may be intentional as an emergency-exit mechanism — but this behavior is undocumented and deviates from the pattern applied to all other user-facing functions.

### BP-05 — Duplicate admin silently consumes a slot

`add-admin` appends to the list without checking for duplicates. Adding the same principal twice occupies two of the five available slots and has no practical effect on privilege (both occurrences satisfy the `index-of` check). Recommend a uniqueness guard before appending.

### BP-06 — `convergence-threshold u0` disables convergence

A threshold of `u0` means `(<= delta u0)` only passes when `new-x == current-x` exactly, which never occurs in fixed-point integer arithmetic until the sequence stabilizes at a fixed point (if it does within 384 steps). Effectively disables convergence detection. Minimum safe value is `u1`.

### BP-07 — No governance event logging

None of the admin functions emit `(print ...)` events. Fee changes, amplification updates, admin additions/removals, and contract reassignments leave no on-chain log beyond the raw transaction. Off-chain monitoring must index `define-public` call receipts rather than structured events, which is harder and error-prone.

### BP-08 — String error codes vs. uint error codes

All `(err "...")` returns use string literals. While readable, Clarity community convention (SIP-010, most DeFi contracts) prefers `uint` error codes (e.g., `(err u401)`) for consistency, lower encoding cost, and easier error matching in caller contracts. This is informational — the current approach is valid Clarity.
