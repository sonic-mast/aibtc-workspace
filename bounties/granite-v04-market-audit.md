# Granite Finance v0-4-market: Static Analysis Audit

**Contract:** `SP1A27KFY4XERQCCRCARCYD1CC5N7M6688BSYADJ7.v0-4-market`  
**Source:** https://api.hiro.so/v2/contracts/source/SP1A27KFY4XERQCCRCARCYD1CC5N7M6688BSYADJ7/v0-4-market  
**Lines:** 1,661  
**Auditor:** Sonic Mast (`bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47`)  
**Date:** 2026-06-05

---

## 1. State Model

### `define-data-var`

| Name | Type | Default | Mutated by |
|---|---|---|---|
| `pause-liquidation` | `bool` | `false` | `set-pause-liquidation` (DAO only) |
| `max-confidence-ratio` | `uint` | `u1000` (10% of BPS) | `set-max-confidence-ratio` (DAO only) |

### `define-map`

| Map | Key | Value | Purpose |
|---|---|---|---|
| `liquidation-grace-periods` | `uint` (asset ID or sentinel) | `uint` (block timestamp) | Per-asset and global liquidation grace windows; `GLOBAL-LIQUIDATION-GRACE-ID=100` is the global sentinel |
| `index-cache` | `{ timestamp: uint, aid: uint }` | `{ index: uint, lindex: uint }` | Per-block accrual index cache — keyed by `stacks-block-time` so entries expire at each new block |
| `last-update` | `{ type: (buff 1), ident: (buff 32) }` | `uint` | Most-recently-accepted oracle timestamp per feed; lower bound for the staleness guard in `oracle-timestamp-fresh` |

### Constants (asset IDs, paired underlying → zToken)

```
STX=0, zSTX=1
sBTC=2, zsBTC=3
stSTX=4, zstSTX=5
USDC=6, zUSDC=7
USDH=8, zUSDH=9
stSTXbtc=10, zstSTXbtc=11
```

zTokens are vault receipt tokens representing liquidity positions. Underlying ID = zToken ID − 1. The mapping is used in `vault-accrue`, `vault-deposit`, `vault-redeem`, and oracle callcode resolution.

**Precision constants:**  
`BPS = 10000` (basis points scale)  
`INDEX-PRECISION = 1e12` (interest index scale)

---

## 2. Function Inventory

### Read-Only Functions

| Function | Authority | Returns | Notes |
|---|---|---|---|
| `get-pause-liquidation` | Open | `(ok bool)` | |
| `get-liquidation-grace-end` | Open | `(ok uint)` | Global grace window end timestamp |
| `get-liquidation-grace-period-asset id` | Open | `(ok uint)` | Per-asset grace window end |
| `get-max-confidence-ratio` | Open | `(ok uint)` | Pyth confidence ratio threshold |
| `oracle-last-update feed` | Open | `uint` | Last accepted timestamp for a feed |
| `get-cached-indexes aid` | Open | `(optional {index, lindex})` | Current-block cache only; returns `none` if not yet accrued this block |

### Public Functions — DAO-Gated (`tx-sender == .dao-executor`)

| Function | Pre-conditions | Mutations |
|---|---|---|
| `set-pause-liquidation paused grace-period` | DAO auth | `pause-liquidation`; `liquidation-grace-periods GLOBAL-LIQUIDATION-GRACE-ID` (written only on unpause transition) |
| `set-liquidation-grace-period id grace-period` | DAO auth | `liquidation-grace-periods id` |
| `set-max-confidence-ratio ratio` | DAO auth; `ratio <= BPS` | `max-confidence-ratio` |

### Public Functions — Open (EOA-only via `contract-caller == tx-sender`)

| Function | Key Pre-conditions | State Mutations | External Calls |
|---|---|---|---|
| `call-ststx-ratio` | None | None | `.block-info-nakamoto-ststx-ratio-v2 get-ststx-ratio-v3` |
| `collateral-add ft amount price-feeds` | `contract-caller == tx-sender`; collateral enabled | `index-cache`, `last-update` (via feed writes); `.v0-market-vault collateral-add` | `write-feeds` (Pyth contracts), `.v0-assets`, `.v0-egroup`, `.v0-market-vault` |
| `collateral-remove ft amount receiver price-feeds` | `amount > 0`; health check if debt present | Same as above + `.v0-market-vault collateral-remove` | Same |
| `supply-collateral-add ft amount min-shares price-feeds` | `contract-caller == tx-sender`; `amount > 0` | `index-cache`, `last-update`; `.v0-market-vault collateral-add` | `ft transfer`, vault deposit (via non-standard `as-contract?`/`with-stx`/`with-ft` pattern), oracle contracts |
| `collateral-remove-redeem ft amount min-underlying receiver price-feeds` | zToken only (checked via `underlying-id <= stSTXbtc`) | Same as `collateral-remove` + vault redeem | `collateral-remove`, `vault-redeem` |
| `borrow ft amount receiver price-feeds` | `contract-caller == tx-sender`; `amount > 0`; debt enabled for asset; not same block as previous borrow; health check with future debt mask | `index-cache`, `last-update`; `.v0-market-vault debt-add-scaled` | Oracle, `vault-system-borrow`, `.v0-market-vault` |
| `repay ft amount on-behalf-of` | `contract-caller == tx-sender`; `amount > 0`; must have positive scaled debt | `index-cache`; `.v0-market-vault debt-remove-scaled` | `vault-system-repay`, `.v0-market-vault` |
| `liquidate borrower coll-ft debt-ft debt-amount min-collateral price-feeds` | `contract-caller == tx-sender`; `debt-amount > 0`; position LTV ≥ `ltv-liq-partial`; not same block as borrower's last borrow | `index-cache`, `last-update`; `.v0-market-vault debt-remove-scaled`; `.v0-market-vault collateral-remove`; bad-debt socialization (conditional) | Oracle contracts, vaults, `.v0-market-vault`, `socialize-debt-asset` fold |
| `liquidate-multi positions` | Delegates to `liquidate` per position | Same as `liquidate` per position | `call-liquidate` → `liquidate` |
| `liquidate-redeem borrower coll-ft debt-ft ...` | zToken only; via `liquidate` delegation | Same as `liquidate` + vault redeem | `liquidate`, `vault-redeem` |

---

## 3. Post-Condition Coverage Matrix

Post-conditions a caller should attach to protect against unexpected behavior:

| Function | Token Movements | Recommended Post-Conditions |
|---|---|---|
| `collateral-add ft amount` | Caller → vault: `amount` units of `ft` (via market re-delegation) | `ft-assert-eq: caller -= amount` |
| `collateral-remove ft amount receiver` | Vault → receiver: up to `amount` zTokens | `ft-assert-le: receiver += amount` |
| `supply-collateral-add ft amount min-shares` | Caller → vault: `amount` underlying; vault → caller: `shares-minted` zTokens | `ft-assert-eq: caller -= amount`; `ft-assert-ge: caller += min-shares` |
| `collateral-remove-redeem ft amount min-underlying receiver` | zTokens removed from collateral; underlying sent to receiver | `ft-assert-ge: receiver += min-underlying` |
| `borrow ft amount receiver` | Vault → receiver: `amount` | `ft-assert-ge: receiver += amount` |
| `repay ft amount on-behalf-of` | Caller → vault: `amount-to-repay` (capped at actual debt, may be < `amount`) | `ft-assert-le: caller -= amount` |
| `liquidate coll-ft debt-ft debt-amount min-collateral` | Liquidator → vault: `debt-to-repay`; vault → liquidator: `coll-final` | `ft-assert-ge: liquidator += min-collateral-expected`; `ft-assert-le: liquidator -= debt-amount` |
| `liquidate-redeem ...` | Same as liquidate + zToken redemption | `ft-assert-ge: receiver += min-underlying` |

**Note:** All token flows pass through vault contracts, not the market directly. Post-conditions should reference the specific FT contract for each asset, not `.v0-4-market`.

---

## 4. Authority / Access-Control Matrix

| Capability | Authority | Mechanism |
|---|---|---|
| Pause/unpause liquidations | DAO only | `check-dao-auth`: `(is-eq tx-sender .dao-executor)` |
| Set per-asset liquidation grace | DAO only | Same |
| Set oracle confidence threshold | DAO only | Same |
| Add/remove collateral | EOA (tx-sender) only | `(is-eq contract-caller tx-sender)` in each function |
| Borrow | EOA (tx-sender) only | Same |
| Repay (self or on-behalf-of) | EOA (tx-sender) only; payer must be tx-sender | Same; `on-behalf-of` targets the debt holder, but tx-sender sends funds |
| Liquidate | EOA (tx-sender) only | Same; optional `collateral-receiver` redirect |
| Price feed writes | Permissionless | `write-feeds` is private but called with user-supplied Pyth VAA bytes; validated on-chain by Pyth contracts |
| Oracle identity rotation | None | Oracle contract addresses are constants (`TYPE-PYTH` → `SP1CGXWEAMG6P6FT04W66NVGJ7PQWMDAC19R7PJ0Y.pyth-oracle-v4`, `TYPE-DIA` → `SP1G48FZ4Y7JY8G2Z0N51QTCYGBQ6F4J43J77BQC0.dia-oracle`) — no rotation path in this contract |

**Hardcoded privileged principals:**
- `.dao-executor` — sole market configurator
- `SP1CGXWEAMG6P6FT04W66NVGJ7PQWMDAC19R7PJ0Y` — Pyth oracle suite (oracle-v4, storage-v4, decoder-v3, wormhole-core-v4)
- `SP1G48FZ4Y7JY8G2Z0N51QTCYGBQ6F4J43J77BQC0` — DIA oracle
- `SP4SZE494VC2YC5JYG7AYFQ44F5Q4PYV7DVMDPBG` — stSTX ratio provider

---

## 5. Clarity Best-Practice Review

### `tx-sender` vs `contract-caller`
✅ All user-facing mutating functions enforce `(is-eq contract-caller tx-sender) ERR-AUTHORIZATION`, preventing contracts from acting on behalf of EOAs. DAO functions correctly use `tx-sender`.

### `unwrap-panic` / `unwrap-err-panic` in user-facing paths
⚠️ **GF-M03** (see Findings). `accrue-debt-asset` (≈L265) and `accrue-collateral-asset` (≈L295) use `unwrap-panic` on vault accrual inside a `fold`:

```clarity
(define-private (accrue-debt-asset (debt-entry {aid: uint, scaled: uint}) (acc {success: bool}))
  (begin
    (unwrap-panic (accrue-and-cache (get aid debt-entry)))
    acc))
```

If any vault's `accrue` call fails, this panics and propagates as a runtime error through the fold, reaching every user-facing function that calls `accrue-user-debts` or `accrue-user-collateral`: `borrow`, `repay`, `liquidate`, `collateral-add`, `collateral-remove`. Users receive no typed error code.

### Arithmetic overflow in `*` / `+`
`calc-liq-factor-exp` uses `pow factor (/ exp BPS)` where `factor` is bounded to `BPS` (10,000) by `min BPS` in the preceding `calc-liq-factor`. `pow(10000, n)` where `n` is a small integer fits in uint-128. No overflow identified in standard paths.

### `as-contract` usage / principal escalation
⚠️ **GF-I01** (see Findings). `supply-collateral-add` uses `as-contract?` with `with-stx`/`with-ft` compound expressions that are not standard Clarity 1 or 2 syntax:

```clarity
(as-contract? ((with-stx amount))
  (try! (vault-deposit asset-id amount min-shares account)))
```

The contract is deployed and presumably functional, but this construct cannot be audited against the published Clarity specification. It may be a Clarity v3 feature or an internal DSL — Granite should publish documentation or tests clarifying the semantics.

### Trait conformance
✅ `(impl-trait .market-trait.market-trait)` declared. Standard `.ft-trait.ft-trait` used for all fungible token parameters.

### Liquidation invariants
⚠️ **GF-M01**: Graduated liquidation curve broken for non-50% exponents.  
⚠️ **GF-M02**: Oracle staleness check bypassed for future-dated timestamps.

---

## 6. Findings Table

| ID | Severity | Function | Line (approx) | Finding | Recommended fix |
|---|---|---|---|---|---|
| GF-M01 | Medium | `calc-liq-factor-exp` | ≈L710 | Sub-BPS exponent approximated as 0.5 for any `exp < BPS` — graduated liquidation curve incorrect for non-50% tuning | Implement proper fractional-exponent interpolation; or limit supported exponents to `{BPS/2, BPS}` and document the restriction |
| GF-M02 | Medium | `oracle-timestamp-fresh` | ≈L339 | Future-dated oracle timestamps (`ts > stacks-block-time`) set `delta=0`, bypassing the max-staleness check entirely | Add upper bound: reject if `ts > stacks-block-time + MAX-FUTURE-DRIFT` (e.g., 10 minutes in seconds) |
| GF-M03 | Medium | `accrue-debt-asset`, `accrue-collateral-asset` | ≈L265, ≈L295 | `unwrap-panic` in `fold` propagates opaque runtime panic to all user-facing functions if any vault accrual fails | Replace with typed-error fold accumulator: `{ success: bool, err: (optional uint) }`; surface typed ERR-ACCRUE-FAILED |
| GF-L01 | Low | `collateral-add` | ≈L1012 | No `(asserts! (> amount u0) ERR-AMOUNT-ZERO)` — zero-amount collateral operations reach `.v0-market-vault`; `supply-collateral-add` and `repay` do have this check | Add `(asserts! (> amount u0) ERR-AMOUNT-ZERO)` at function entry, matching `supply-collateral-add` |
| GF-L02 | Low | `liquidate-multi` / `call-liquidate` | ≈L1603 | Passes `none` for price-feeds in all batch liquidations — bots must submit a separate Pyth price-update transaction before calling `liquidate-multi` | Document timing requirement explicitly in contract comments; consider a variant that accepts a single shared `price-feeds` list applied before the map |
| GF-I01 | Informational | `supply-collateral-add` | ≈L1168 | `as-contract?` with `with-stx`/`with-ft` patterns are non-standard Clarity 1/2 syntax — static analysis tools and auditors cannot verify this section against the published Clarity spec | Publish specification or test suite covering the `as-contract?`/`with-stx`/`with-ft` semantics; link to Clarity v3 changelog if applicable |
| GF-I02 | Informational | Module constants | ≈L43 | Oracle contract addresses are constants with no rotation mechanism — a compromised oracle requires a new market contract deployment | Document the upgrade path in Granite docs; DAO should maintain a deployment script for successor contracts |

### Responsible Disclosure
No high or critical severity findings were identified. Private disclosure to the Granite Finance team is not required per bounty rules.

### Summary
The contract implements a graduated liquidation mechanism with Pyth/DIA oracle integration and per-block index caching. The core accounting logic (health factor, scaled debt, collateral valuation, bad-debt socialization) is sound. The three medium findings relate to edge-case approximation accuracy (GF-M01), oracle freshness logic (GF-M02), and error propagation ergonomics (GF-M03). None enable unauthorized fund extraction or position manipulation under normal oracle operation.
