---
name: Wallet unlock requires literal values; mnemonic needs space normalization
description: MCP params don't expand shell vars; AIBTC_MNEMONIC may have extra internal spaces that fail wallet_import
type: feedback
---

MCP tool calls take literal string values — env var placeholders are passed verbatim, not shell-expanded. Always read values via bash first:

```bash
echo "$AIBTC_WALLET_PASSWORD" | cat   # password
echo "$AIBTC_MNEMONIC" | tr -s ' ' | xargs echo   # mnemonic — normalizes extra spaces
```

**Mnemonic gotcha:** `AIBTC_MNEMONIC` contains extra internal spaces (e.g., triple spaces after some words). Passing the raw value to `wallet_import` returns `Invalid mnemonic phrase (WALLET_ERROR)`. Normalize with `tr -s ' '` before using.

**Why:** Raw env var expansion fails silently with misleading error; mnemonic space issue is not obvious from the error message alone.
**How to apply:** Before every `wallet_import` + `wallet_unlock` sequence, retrieve literal values from bash and normalize the mnemonic.
