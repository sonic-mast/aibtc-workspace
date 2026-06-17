# Audit: Velar univ2-core AMM — Static Analysis Report

**Contract:** `SP1Y5YSTAHZ88XYK1VPDH24GY0HPX5J4JECTMY4A1.univ2-core`  
**Protocol:** Velar — UniV2-style AMM  
**Source verified:** https://api.hiro.so/v2/contracts/source/SP1Y5YSTAHZ88XYK1VPDH24GY0HPX5J4JECTMY4A1/univ2-core  
**Auditor:** sonic-mast (`bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47`)  
**Audit type:** Static analysis (no on-chain execution)  
**Source length:** 20,029 chars (~629 lines Clarity)  

---

## 1. State Model

### data-var

| Variable | Type | Initial | Mutation authority | Mutated by |
|---|---|---|---|---|
| `owner` | principal | `tx-sender` (deployer) | owner only | `set-owner` |
| `protocol-fee-to` | principal | `tx-sender` (deployer) | owner only | `set-protocol-fee-to` |
| `share-fee-to` | principal | `.univ2-share-fee-to` | owner only | `set-share-fee-to` |
| `pool-id` | uint | `u0` | private only | `next-pool-id` (auto-increment) |

### data-map

| Map | Key | Value | Purpose |
|---|---|---|---|
| `pools` | `uint` (pool ID) | `{symbol, token0, token1, lp-token, reserve0, reserve1, swap-fee, protocol-fee, share-fee, block-height, burn-block-height}` | All pool state |
| `index` | `{token0: principal, token1: principal}` | `uint` | Pool ID lookup by canonical token pair order |
| `lp-tokens` | `principal` | `bool` | Registered LP token set |
| `revenue` | `uint` | `{token0: uint, token1: uint}` | Accumulated protocol fee revenue per pool |

### Fee parameters (all stored as `{num: uint, den: uint}` fractions)

- **swap-fee**: fraction of input that passes through to the swap. Default example: `{num: 998, den: 1000}` = 0.2% LP fee.
- **protocol-fee**: fraction of the swap fee that goes to protocol. Max: `{num: 500, den: 1000}` = 50%.
- **share-fee**: fraction of protocol fee routed to `share-fee-to`. Range: 0–100%.

### Constants

| Constant | Value | Role |
|---|---|---|
| `MAX-SWAP-FEE` | `{num: 995, den: 1000}` | Anti-rug: swap-fee.num must be ≥ 995 (max 0.5% taken from input) |
| `MAX-PROTOCOL-FEE` | `{num: 500, den: 1000}` | Anti-rug: protocol-fee.num must be ≤ 500 (max 50% of swap fee) |
| Error codes | `u100`–`u113` | Pre/post condition identifiers |

---

## 2. Function Inventory

### Admin (owner-only)

**`set-owner(new-owner principal)`**
- Authority: `check-owner` (tx-sender == owner data-var)
- Pre-conditions: caller == owner
- State mutations: `owner ← new-owner`
- External calls: none
- Note: No two-step ownership transfer. New owner takes effect immediately. If wrong address is passed, contract is permanently bricked for admin operations.

**`set-protocol-fee-to(new-protocol-fee-to principal)`**
- Authority: owner
- State mutations: `protocol-fee-to ← new-protocol-fee-to`

**`set-share-fee-to(new-share-fee-to principal)`**
- Authority: owner
- State mutations: `share-fee-to ← new-share-fee-to`

**`update-swap-fee(id uint, fee {num uint, den uint})`**
- Authority: owner
- Pre-conditions: `check-swap-fee(fee, MAX-SWAP-FEE)` — fee.den must equal 1000 AND fee.num ≥ 995
- Anti-rug: swap fee cannot exceed 0.5% of input (fee.num ≥ 995/1000 guarantees ≥99.5% of input reaches the x*y=k invariant)
- State mutations: `pools[id].swap-fee ← fee`

**`update-protocol-fee(id uint, fee {num uint, den uint})`**
- Authority: owner
- Pre-conditions: `check-protocol-fee(fee, MAX-PROTOCOL-FEE)` — fee.den must equal 1000 AND fee.num ≤ 500
- State mutations: `pools[id].protocol-fee ← fee`

**`update-share-fee(id uint, fee {num uint, den uint})`**
- Authority: owner
- Pre-conditions: `check-share-fee(fee)` — fee.den must equal 1000 AND fee.num ≤ 1000
- State mutations: `pools[id].share-fee ← fee`

**`create(token0, token1, lp-token, swap-fee, protocol-fee, share-fee)`**
- Authority: owner
- Pre-conditions asserted (err-create-preconditions):
  - t0 ≠ t1
  - No existing pool for the pair (in either ordering)
  - lp-token not already registered in lp-tokens
  - All fee numerators ≤ denominators
  - swap-fee passes anti-rug check (den == 1000, num ≥ 995)
  - protocol-fee passes anti-rug check (den == 1000, num ≤ 500)
  - share-fee passes anti-rug check (den == 1000, num ≤ 1000)
- State mutations: map-set `pools[id]`, `index[{t0,t1}]`, `lp-tokens[lp]`, `revenue[id]`
- External calls: `token0.get-symbol()`, `token1.get-symbol()` (for symbol construction)
- Post-conditions: none explicit

### User-callable

**`mint(id, token0, token1, lp-token, amt0, amt1)`**
- Authority: any (tx-sender becomes user)
- Pre-conditions (err-mint-preconditions):
  - Pool's recorded token0/token1/lp-token match the passed contracts
  - amt0 > 0, amt1 > 0
  - `liquidity = calc-mint(amt0, amt1, r0, r1, total-supply) > 0`
- External calls:
  - `token0.transfer(amt0, user → protocol)` — pulls tokens from user
  - `token1.transfer(amt1, user → protocol)` — pulls tokens from user
  - `lp-token.mint(liquidity, user)` — mints LP tokens to user
- State mutations: `update-reserves(id, r0+amt0, r1+amt1)`
- Post-conditions (err-mint-postconditions):
  - `(total-supply + liquidity) * (r0 + amt0) > 0`
  - `(total-supply + liquidity) * (r1 + amt1) > 0`
  - (Overflow protection for subsequent burn calculations)
- calc-mint: If `total-supply == 0`, returns `sqrti(amt0 * amt1)`. Otherwise `min(amt0 * ts / r0, amt1 * ts / r1)`.

**`burn(id, token0, token1, lp-token, liquidity)`**
- Authority: any (caller must hold LP tokens)
- Pre-conditions (err-burn-preconditions):
  - Token addresses match pool
  - liquidity > 0
  - amt0 = `(liquidity * r0) / total-supply > 0`
  - amt1 = `(liquidity * r1) / total-supply > 0`
- External calls:
  - `token0.transfer(amt0, protocol → user)` — sends tokens to user
  - `token1.transfer(amt1, protocol → user)` — sends tokens to user
  - `lp-token.burn(liquidity, user)` — burns LP tokens from user
- State mutations: `update-reserves(id, r0-amt0, r1-amt1)`
- Post-conditions: none explicit

**`swap(id, token-in, token-out, share-fee-to0, amt-in, amt-out)`**
- Authority: any
- Pre-conditions (err-swap-preconditions): complex — see below
- External calls:
  - `token-in.transfer(amt-in, user → protocol)` — pulls input
  - `token-out.transfer(amt-out, protocol → user)` — sends output
  - IF amt-fee-share > 0: `token-in.transfer(amt-fee-share, protocol → share-fee-to)` + `share-fee-to0.receive(id, is-token0, amt-fee-share)`
- State mutations: `update-reserves(id, b0, b1)`, `update-revenue(id, is-token0, amt-fee-rest)`
- Post-conditions (err-swap-postconditions): `a * b >= k` (x*y invariant preserved)
- Note: `amt-out` is caller-supplied. No on-chain computation of expected output. Slippage control is the caller's responsibility.

**Swap pre-conditions detail:**
- token-in and token-out are pool's tokens (in any order, not same)
- share-fee-to0 matches `get-share-fee-to` state variable
- amt-in > 0, amt-out > 0
- amt-in-adjusted > 0 (fee calculation produces positive adjusted amount)
- Fee decomposition: `amt-in = amt-in-adjusted + amt-fee-lps + amt-fee-share + amt-fee-rest` (asserted)
- Balance values > 0: b0, b1, a, b all positive

**`collect(id, token0, token1)`**
- Authority: `check-protocol-fee-to` — caller must equal `protocol-fee-to` data-var
- Pre-conditions: caller == protocol-fee-to, token addresses match pool
- External calls:
  - IF `revenue.token0 > 0`: `token0.transfer(amt0, protocol → user)`
  - IF `revenue.token1 > 0`: `token1.transfer(amt1, protocol → user)`
- State mutations: `reset-revenue(id)` → sets revenue[id] = {token0: u0, token1: u0}
- Post-conditions: none explicit

### Read-only

| Function | Returns |
|---|---|
| `get-owner` | current owner principal |
| `get-protocol-fee-to` | current protocol fee recipient |
| `get-share-fee-to` | current share fee contract |
| `get-nr-pools` | total pool count (pool-id var) |
| `get-pool(id)` | optional pool struct |
| `do-get-pool(id)` | pool struct (panics if none) |
| `get-pool-id(t0, t1)` | optional uint (canonical order) |
| `lookup-pool(t0, t1)` | optional {pool, flipped} (tries both orderings) |
| `do-get-revenue(id)` | revenue struct (panics if none) |
| `check-swap-fee(fee, guard)` | bool |
| `check-protocol-fee(fee, guard)` | bool |
| `check-share-fee(fee)` | bool |
| `calc-mint(amt0, amt1, r0, r1, ts)` | uint (LP liquidity) |
| `min(a, b)` | uint |
| `calc-burn(liquidity, r0, r1, ts)` | {amt0, amt1} |
| `calc-swap(amt-in, swap-fee, protocol-fee, share-fee)` | fee breakdown tuple |
| `update-swap-fee` / `update-protocol-fee` / `update-share-fee` | (check-* helpers) |

---

## 3. Post-Condition Coverage Matrix

| Function | Transfers IN | Transfers OUT | LP mint | LP burn | Reserve Δ | Revenue Δ | On-chain post-cond |
|---|---|---|---|---|---|---|---|
| `create` | none | none | none | none | init → 0 | init → {0,0} | none |
| `mint` | token0 user→protocol, token1 user→protocol | LP user (mint) | ✅ | ❌ | +amt0, +amt1 | none | overflow guard |
| `burn` | LP user (burn) | token0 protocol→user, token1 protocol→user | ❌ | ✅ | −amt0, −amt1 | none | none |
| `swap` | token-in user→protocol, (fee-share protocol→share-fee-to) | token-out protocol→user | ❌ | ❌ | b0, b1 | +fee-rest | x*y≥k |
| `collect` | none | token0 protocol→user (if >0), token1 protocol→user (if >0) | ❌ | ❌ | none | reset → {0,0} | none |

---

## 4. Findings

### F1 — Owner is a single EOA with no timelocks (MEDIUM)
**Affected functions:** `set-owner`, `set-protocol-fee-to`, `set-share-fee-to`, `update-swap-fee`, `update-protocol-fee`, `update-share-fee`, `create`

The `owner` variable is set at deploy time to `tx-sender` with no multisig or timelock. All fee parameter changes take effect immediately in the same block. If the owner key is compromised:
- Fees cannot be set above anti-rug ceilings (0.5% swap fee, 50% protocol cut)
- New pools can be created with adversarial LP token contracts
- `set-owner` allows immediate transfer to any arbitrary principal, including contracts

**Recommendation:** Use a multisig or DAO as owner. `set-owner` should require the new owner to accept (two-step transfer) to prevent accidental misdirection.

### F2 — `do-get-pool` uses `unwrap-panic` — callers must validate IDs (LOW)
**Affected functions:** `mint`, `burn`, `swap`, `collect`, `update-swap-fee`, `update-protocol-fee`, `update-share-fee`

`do-get-pool` calls `unwrap-panic`, which aborts the transaction if the pool ID doesn't exist. Since Clarity transactions are atomic and isolated, this won't corrupt contract state — but any integrating protocol that passes an unvalidated pool ID will receive an `ABR` abort (not an err tuple). Callers should use `get-pool` (which returns `(optional ...)`) and handle the `none` case explicitly.

### F3 — Fee denominator hard-coded to 1000 limits fee granularity (NOTE)
**Affected functions:** `update-swap-fee`, `update-protocol-fee`, `update-share-fee`, `create`

All fee anti-rug checks assert `fee.den == 1000`. This constrains fee precision to 0.1% increments. A fee of 997/1000 (0.3%) is valid; a fee of 3/1000 (0.3%) in a different encoding would pass math checks but fail the denominator gate. Integrators must use denominator 1000.

### F4 — `burn` has no post-condition: zero-output burns revert in precondition only (LOW)
**Affected:** `burn`

`calc-burn` does integer division: `liquidity * reserve / total-supply`. For very small LP amounts, this can round to 0 for one or both tokens. The pre-condition `> amt0 u0` and `> amt1 u0` catches this and reverts. However, there is no post-condition verifying that reserves decreased by exactly the computed amounts. The transfer of token0/token1 out is not validated against a reserve snapshot. This is a minor discrepancy with the stated post-condition style of other functions.

### F5 — `swap` `share-fee-to0` receives arbitrary trait call after funds transfer (LOW)
**Affected:** `swap`

The swap function transfers `amt-fee-share` from the protocol to `get-share-fee-to` and then calls `share-fee-to0.receive(...)`. The `share-fee-to` address is validated by comparing it to the `get-share-fee-to` state variable on each swap call (not cached). If the owner changes `share-fee-to` between the validation and the trait call within the same block, this could route fees to an unintended contract. However, Clarity's single-block execution model means all calls in a block are serialized — the owner cannot interleave a `set-share-fee-to` call in the middle of a user's `swap` call. Risk is limited to the owner pre-emptively changing `share-fee-to` in the same block as a pending swap.

### F6 — `calc-mint` initial liquidity uses `sqrti` without minimum liquidity burn (NOTE)
**Affected:** `mint` (first liquidity provision)

On first mint (`total-supply == 0`), liquidity = `sqrti(amt0 * amt1)`. Uniswap V2 burns `MINIMUM_LIQUIDITY` (1000) to address(0) on first mint to protect against LP share manipulation attacks. Velar does not implement this burn. This means the first liquidity provider can potentially manipulate the initial LP price if they also own the LP token contract — but since LP token creation is owner-controlled (`create` is owner-only), this risk is limited to trusted pool creators.

### F7 — No sync/skim functions (NOTE)
The contract includes a comment: "~Not implementable since tokens for all pools are owned by a single contract (and we can't iterate over pools)." All pools share the same principal (`as-contract tx-sender`). This means donated tokens (sent directly without going through mint/swap) accumulate without increasing reserves. While Velar is aware of this, it creates a discrepancy between actual token balances held by the contract and the `reserve0`/`reserve1` values tracked in `pools`. No path to recover donated tokens exists.

---

## 5. Summary

| Severity | Count | IDs |
|---|---|---|
| MEDIUM | 1 | F1 (owner centralization) |
| LOW | 3 | F2, F4, F5 |
| NOTE | 3 | F3, F6, F7 |
| CRITICAL | 0 | — |

**Overall assessment:** The contract is a faithful Clarity port of Uniswap V2 with well-structured anti-rug mechanisms capping owner fee extraction. The core x*y=k invariant is enforced in `swap` post-conditions. The primary risk is owner-key centralization (F1) — all trust rests on the deployer key. No critical vulnerabilities found in the fee math, reserve accounting, or LP mint/burn calculations.
