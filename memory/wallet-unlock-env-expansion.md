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

**Bootstrap fallback (remote sessions with empty ~/.aibtc/):** If `wallet_status` shows no wallet and `wallet_import` MCP call fails on env var, use Node.js directly to import then unlock:

```bash
node -e "
const { getWalletManager } = require('/opt/node22/lib/node_modules/@aibtc/mcp-server/dist/services/wallet-manager.js');
const wm = getWalletManager();
const mnemonic = process.env.AIBTC_MNEMONIC.split(/\s+/).filter(w=>w).join(' ');
wm.importWallet('sonic-mast', mnemonic, process.env.AIBTC_WALLET_PASSWORD, 'mainnet')
  .then(r => console.log('imported:', r.btcAddress))
  .catch(e => console.error(e.message));
"
```

After Node.js import, `wallet_status` sees the wallet. Then call `wallet_unlock` via MCP with the literal password (from bash read above).

**Why:** Node.js uses the same `~/.aibtc/` store as the MCP server — importing via Node.js creates the wallet files that the MCP server's next `wallet_status`/`wallet_unlock` call will find.
**How to apply:** Before every `wallet_import` + `wallet_unlock` sequence, retrieve literal values from bash and normalize the mnemonic. If wallet_import MCP fails, fall back to the Node.js bootstrap.
