# Zest Protocol pool-borrow-v2-3: Static Analysis Audit

**Contract:** `SP2VCQJGH7PHP2DJK7Z0V48AGBHQAW3R3ZW1QF4N.pool-borrow-v2-3`  
**Source:** https://api.hiro.so/v2/contracts/source/SP2VCQJGH7PHP2DJK7Z0V48AGBHQAW3R3ZW1QF4N/pool-borrow-v2-3  
**Lines:** 1,005  
**Auditor:** Sonic Mast (`bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47`)  
**Date:** 2026-06-07

---

## 1. State Model

### `define-data-var`

| Name | Type | Default | Mutated by |
|---|---|---|---|
| `last-user-id` | `uint` | `u0` | `supply` (increments on every call) |
| `configurator` | `principal` | `tx-sender` (deployer) | `set-configurator` (configurator only) |

### `define-map`

| Map | Key | Value | Purpose |
|---|---|---|---|
| `users-id` | `uint` | `principal` | Ordered log of suppliers; ID → principal. Appended on every `supply` call — the same user can appear under multiple IDs. |
| `approved-contracts` | `principal` | `bool` | Access-control allowlist for callers of all public write functions. |

### Traits Used

| Trait | Purpose |
|---|---|
| `ft` | Standard fungible token interface |
| `ft-mint-trait` | Mintable token (a-tokens) |
| `a-token` | Zest aToken (redeemable receipt token) |
| `flash-loan` | Flash loan callback interface |
| `oracle-trait` | Price oracle interface |
| `redeemeable-trait` | Pool liquidity receipt (cumulate-balance, mint, burn) |

---

## 2. Function Inventory

### Read-Only Functions

| Function | Returns | Notes |
|---|---|---|
| `get-user(id)` | `(optional principal)` | Lookup by sequential ID |
| `get-last-user-id` | `uint` | Current counter value |
| `validate-use-as-collateral(...)` | `(ok bool)` | Isolation mode + LTV zero check |
| `validate-assets(assets)` | `(ok {...})` | Verifies caller-provided asset list against stored reserve data |
| `check-assets(asset, ret)` | `(response {...} uint)` | Fold helper for validate-assets |
| `get-asset-isolation-mode-debt(collateral, borrowed)` | `uint` | Reads from pool-reserve-data-3 |
| `mul-to-fixed-precision(amount, decimals, price)` | `uint` | Delegates to pool-0-reserve-v2-0 |
| `get-reserve-state(asset)` | `(response reserve-state uint)` | Delegates to pool-0-reserve-v2-0 |
| `get-user-reserve-data(user, asset)` | `user-reserve-data` | Delegates to pool-0-reserve-v2-0 |
| `get-borroweable-isolated` | `(list 100 principal)` | Delegates to pool-0-reserve-v2-0 |
| `get-assets` | `(list 100 principal)` | Delegates to pool-reserve-data |
| `get-asset-e-mode-type(asset)` | `(buff 1)` | Delegates to pool-0-reserve-v2-0 |
| `get-user-e-mode(user)` | `(buff 1)` | Delegates to pool-0-reserve-v2-0 |
| `is-in-e-mode(user)` | `bool` | Delegates to pool-0-reserve-v2-0 |
| `is-configurator(caller)` | `bool` | Checks var-get configurator |
| `is-approved-contract(contract)` | `(response bool uint)` | Reads approved-contracts map |
| `filter-asset(asset, ret)` | `{filter-by, agg}` | Fold helper for remove-borroweable-isolated |
| `can-enable-e-mode(user, e-mode-type)` | `(response ...)` | Delegates to pool-0-reserve-v2-0 |

### Public Functions — Configurator-Gated

| Function | Effect |
|---|---|
| `set-configurator(new)` | Transfers admin rights; checks `is-eq tx-sender (var-get configurator)` |
| `init(a-token, asset, decimals, supply-cap, borrow-cap, oracle, strategy)` | Initializes a reserve with all fields; safe defaults (borrowing disabled, not frozen) |
| `set-reserve(asset, state)` | Full state override on any reserve — no validation on field values |
| `set-borrowing-enabled(asset, enabled)` | Toggle borrowing on a reserve |
| `set-usage-as-collateral-enabled(asset, enabled, ltv, threshold, bonus)` | Toggle collateral usage and update LTV params |
| `add-isolated-asset(asset, debt-ceiling)` | Marks an asset as isolated and sets debt ceiling |
| `add-asset(asset)` | Adds asset to protocol asset list |
| `remove-asset(asset)` | Removes asset from protocol asset list |
| `remove-isolated-asset(asset)` | Removes isolated status from an asset |
| `set-borroweable-isolated(asset)` | Adds an asset to the isolated-borrowable list |
| `remove-borroweable-isolated(asset)` | Removes an asset from the isolated-borrowable list |
| `set-freeze-end-block(asset, end-block)` | Sets per-asset freeze end block |
| `set-grace-period-time(asset, time)` | Sets per-asset liquidation grace period |
| `set-grace-period-enabled(asset, enabled)` | Enables/disables liquidation grace period |
| `set-e-mode-type-enabled(e-mode-type, enabled)` | Enables/disables an e-mode type |
| `set-e-mode-type-config(e-mode-type, ltv, threshold)` | Sets LTV and threshold for an e-mode type |
| `set-asset-e-mode-type(asset, e-mode-type)` | Assigns an asset to an e-mode category |
| `set-approved-contract(contract, enabled)` | Adds/removes contracts from the caller allowlist |

### Public Functions — Approved-Contract-Gated

| Function | Effect |
|---|---|
| `supply(lp, pool-reserve, asset, amount, owner)` | Deposit into pool; mint a-tokens; validate caps and collateral mode |
| `withdraw(pool-reserve, asset, lp, oracle, assets, amount, owner)` | Redeem a-tokens; validates health factor; transfer asset out |
| `borrow(pool-reserve, oracle, asset-to-borrow, lp, assets, amount, fee-calculator, interest-rate-mode, owner)` | Validates collateral, caps, and isolation mode; transfers borrowed asset |
| `repay(asset, amount-to-repay, on-behalf-of, payer)` | Repays outstanding borrow; adjusts isolation debt |
| `liquidation-call(assets, collateral-lp, collateral-to-liquidate, debt-asset, ...)` | Delegates to liquidation-manager-v2-3; adjusts isolation debt |
| `flashloan-liquidation-step-1(receiver, asset, amount, flashloan-script)` | Transfers asset OUT to receiver; **no callback invocation** |
| `flashloan-liquidation-step-2(receiver, asset, amount, flashloan-script)` | Pulls `amount + fee` back from receiver; updates state |
| `set-e-mode(user, assets, new-e-mode-type)` | Changes a user's e-mode; validates active borrows and collateral match |
| `set-user-use-reserve-as-collateral(who, lp-token, asset, enable, oracle, assets)` | Toggles collateral flag; validates health and isolation mode |

---

## 3. Security Findings

### MEDIUM — Split-Step Flash Loan Lacks Atomicity Guarantee

**Location:** `flashloan-liquidation-step-1` / `flashloan-liquidation-step-2`

`step-1` transfers `amount` to `receiver` without invoking a callback and returns `(ok u0)`. `step-2` (a separate public function) pulls back `amount + amount-fee` and updates state. The two steps are not linked by any nonce, session ID, or block-height guard — any approved contract can call `step-1` and then independently call `step-2` with different `amount` and `receiver` values, or call `step-1` twice before calling `step-2` once.

The design delegates atomicity responsibility entirely to approved callers. The `(asserts! (>= available-liquidity-before amount))` check in `step-2` uses the liquidity *before* repayment, which is correct, but it doesn't enforce that `step-2` is called by the same caller that called `step-1`, in the same block, or with the same parameters.

**Standard practice:** Atomic callbacks within a single transaction — the pool transfers funds, immediately calls the receiver's `execute-operation`, and then verifies the balance has been restored. The split-step pattern is safe only when callers are fully trusted and their logic is verified to call both steps atomically within one transaction.

**Risk:** Low in practice (approved-contracts allowlist is the guard), but the design creates fragility: a new approved caller that handles the steps non-atomically could drain the pool.

**Recommendation:** Enforce in `step-2` that `available-liquidity-before` equals the liquidity at the time `step-1` was called, or switch to an atomic callback model. At minimum, document the expected call pattern in the contract header with `@pre-condition`.

---

### MEDIUM — Configurator is a Single EOA with No Timelock

**Location:** `(define-data-var configurator principal tx-sender)` and all `set-*` admin functions

The `configurator` data var is initialized to the deployer's `tx-sender`. A single principal can immediately:
- Call `set-reserve` to override any reserve's `liquidation-threshold` to `u0` (disabling liquidations)
- Call `set-usage-as-collateral-enabled` with arbitrary LTV values
- Call `set-approved-contract` to whitelist a malicious contract
- Transfer configurator rights via `set-configurator`

None of these actions require a timelock, multi-sig confirmation, or DAO governance vote. A compromised configurator key could drain the protocol in a single transaction.

**Risk:** High impact if configurator is an externally owned account; lower if it's a multi-sig or governance contract.

**Recommendation:** Verify the deployed `configurator` principal is a multi-sig or DAO contract (e.g., `.dao-executor`). Add an on-chain assertion or `print` statement in `set-configurator` to make the current principal discoverable without reading storage. Consider a two-step transfer pattern (`propose-configurator` → `accept-configurator`) to prevent accidental or forced transfers.

---

### LOW — `users-id` Map Grows Unboundedly

**Location:** `supply` function, user-id insertion block

On every `supply` call, the contract inserts a new entry into `users-id` with an auto-incremented key, even if the user already exists in the map:

```clarity
(map-insert users-id (var-get last-user-id) owner)
(var-set last-user-id (+ u1 (var-get last-user-id)))
```

`map-insert` returns `false` when the key already exists — but the key here is the auto-incrementing `last-user-id`, so it always succeeds. A single user who calls `supply` 1,000 times will generate 1,000 map entries, all mapping distinct IDs → same principal.

There is no corresponding `map-delete` and no cleanup path. The `get-user` read-only accepts only an ID; there is no principal → ID reverse lookup, so the map cannot serve as a user registry.

**Risk:** State bloat over time; no direct security impact.

**Recommendation:** Add a `principal → uint` reverse map (`user-ids`) or check whether the user has previously supplied before inserting. If the map is purely an event log, document that intent in comments and make the name reflect it (e.g., `supply-log-id`).

---

### INFORMATIONAL — `fee-calculator` Parameter Declared But Not Used

**Location:** `borrow` function signature

The `borrow` function accepts a `fee-calculator` parameter of type `principal`, but it is not used within this contract. The downstream `update-state-on-borrow` call passes `u0` as the fee:

```clarity
(try! (contract-call? .pool-0-reserve-v2-0 update-state-on-borrow asset-to-borrow owner amount-to-be-borrowed u0))
```

If the intent is for `pool-0-reserve-v2-0` to route fee calculations through the caller-supplied contract, that handoff is missing here. If the parameter is a legacy interface remnant, it should be removed to prevent caller confusion.

**Recommendation:** Either thread `fee-calculator` into the downstream call (verifying it's on an allowlist first) or remove the parameter from the function signature.

---

### INFORMATIONAL — Oracle Validation at Call-Site Is Solid

The `withdraw`, `borrow`, and `liquidation-call` functions all assert:

```clarity
(asserts! (is-eq (contract-of oracle) (get oracle reserve-state)) ERR_INVALID_ORACLE)
```

This prevents oracle substitution attacks: callers cannot supply a different oracle contract than the one registered in reserve data. This pattern is correctly applied in every function that accepts an oracle parameter. No finding.

---

### INFORMATIONAL — `validate-assets` Prevents Asset List Manipulation

The `validate-assets` fold checks that:
1. The caller-supplied list length matches the protocol's registered asset count exactly.
2. Each entry's `asset`, `lp-token`, and `oracle` fields match the stored reserve data for that position.

This is a correct defense against asset injection — callers cannot swap in a different asset or oracle at any list position. The ERR_NON_CORRESPONDING_ASSETS and ERR_INVALID_ASSETS errors are correctly separated. No finding.

---

## 4. Summary

| Severity | Count | Issues |
|---|---|---|
| Critical | 0 | — |
| High | 0 | — |
| Medium | 2 | Split-step flash loan atomicity; single-EOA configurator |
| Low | 1 | users-id map unbounded growth |
| Informational | 3 | Unused fee-calculator param; oracle validation solid; validate-assets solid |

**Overall assessment:** The contract's core borrow/repay/liquidation logic is structurally sound with correct guard ordering (active, not-frozen, cap checks before state mutations). The two medium findings are design-level risks that depend on operational controls (approved-contracts allowlist integrity; configurator key security) rather than code bugs. The split-step flash loan design is the highest-priority item to document or remediate before expanding the approved-contracts set.
