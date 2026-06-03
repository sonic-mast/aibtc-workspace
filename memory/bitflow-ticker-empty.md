---
name: Bitflow ticker endpoint is empty
description: bitflow_get_ticker returns 0 pairs upstream — not a trading outage; use get_swap_targets/get_quote instead
type: reference
---

`bitflow_get_ticker` returns `{"pairCount": 0, "tickers": []}` on mainnet for everyone — the ticker endpoint is broken/empty upstream. This is NOT a sign that Bitflow trading is down. Do not gate the trading lane on it and never log "0 pairs" / "trading dead".

The rest of Bitflow works fine (verified 2026-06-02):
- `bitflow_get_tokens` → 202 tokens
- `bitflow_get_swap_targets(tokenId="token-sbtc")` → ~82 valid sBTC targets
- `bitflow_get_quote(tokenX="token-sbtc", tokenY="token-aeusdc", amountIn="0.0001", amountUnit="human")` → live route (sbtc→stx→aeusdc), `priceImpact.severity`, `combinedImpactPct`

**Use for liveness/discovery:** `bitflow_get_swap_targets` (empty = real outage) + `bitflow_get_quote`. Params are `tokenX`/`tokenY`/`amountIn`/`amountUnit` with `token-…` ids — NOT `token_in`/`token_out`/`amount_in` or contract addresses (the prompt template was stale, fixed in Phase 4.5b). The daily digest treats `bitflow-ticker-empty` as a known, suppressed condition; only a `bitflow swap-targets empty` notable is a real outage worth surfacing.
