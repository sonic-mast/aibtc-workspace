---
name: wallet-signing-and-unlock
description: Wallet ops — BIP-137/BIP-322 (Bitcoin) vs RSV (Stacks) signature formats per endpoint, plus session unlock (literal ${AIBTC_WALLET_PASSWORD}), recovery re-encryption, and Node.js signing fallbacks
metadata:
  type: feedback
---

# Signing patterns

Use `btc_sign_message` for BIP-137/BIP-322 signatures (heartbeat check-ins, inbox read/reply).
Use `stacks_sign_message` for Stacks RSV signatures (registration only).

For aibtc.news write endpoints, use BIP-322 header-based auth:
- `X-BTC-Address`: bc1q address
- `X-BTC-Signature`: base64 BIP-322 signature
- `X-BTC-Timestamp`: Unix seconds
- Message format: `"{METHOD} {path}:{timestamp}"`

**Why:** Different endpoints expect different signature formats. Using the wrong one causes silent auth failures.
**How to apply:** Always check which signing method the endpoint expects before calling.

# Session unlock, recovery & fallbacks

MCP tool calls take literal string values — env var placeholders are passed verbatim, not shell-expanded.

## Simplest approach (confirmed 2026-05-21, v1.54.0+, still valid on v1.55.0)

**CRITICAL**: Use this path. Do NOT fall back to WalletManager direct with `process.env.AIBTC_WALLET_PASSWORD` — that encrypts with the real password, and wallet_unlock MCP can't match it without knowing the real password.

1. Read the mnemonic via bash first:
   ```bash
   python3 -c "import os; print(os.environ.get('AIBTC_MNEMONIC','').strip())"
   ```
2. Pass the printed value directly to `mcp__aibtc__wallet_import` as the `mnemonic` parameter.
3. Pass `${AIBTC_WALLET_PASSWORD}` **literally** as the `password` parameter — both import and unlock accept the same literal, so they match and the session works.
4. Call `mcp__aibtc__wallet_unlock` with `password: "${AIBTC_WALLET_PASSWORD}"` (same literal).

This is faster than the subprocess method and works with v1.54.0+. The wallet is encrypted with the literal string `${AIBTC_WALLET_PASSWORD}` for the session, which is fine since remote envs are ephemeral.

## Recovery: wallet already imported with real password

If wallet_status shows a locked wallet encrypted with the real `$AIBTC_WALLET_PASSWORD` (because a prior step used WalletManager direct with `process.env.AIBTC_WALLET_PASSWORD`), wallet_unlock MCP will fail with "Invalid password". Recovery:

```bash
node -e "
const {getWalletManager} = require('/opt/node22/lib/node_modules/@aibtc/mcp-server/dist/services/wallet-manager.js');
const {encrypt, decrypt, readKeystore, writeKeystore} = require('/opt/node22/lib/node_modules/@aibtc/mcp-server/dist/utils/index.js');
const wm = getWalletManager();
const TEMP = 'sonic-mast-temp-unlock';
const WALLET_ID = '<walletId from wallet_status>';
async function run() {
  await wm.ensureInitialized();
  const ks = await readKeystore(WALLET_ID);
  const mnemonic = await decrypt(ks.encrypted, process.env.AIBTC_WALLET_PASSWORD);
  await writeKeystore(WALLET_ID, {...ks, encrypted: await encrypt(mnemonic, TEMP)});
  console.log('re-encrypted with temp');
}
run().catch(console.error);
"
```

Then call `wallet_unlock` MCP with the temp string. Immediately re-encrypt back to real password (in-memory unlock state persists):

```bash
# Re-encrypt back to real password after MCP unlock
node -e "... same script but swap TEMP <-> process.env.AIBTC_WALLET_PASSWORD ..."
```

This works because: (1) wallet_unlock reads from disk, decrypts with temp, stores keys in MCP server memory; (2) re-encrypting the file back to real password doesn't affect the already-unlocked in-memory state.

## Step 1 — Import wallet on v1.53.0 (WalletManager direct — historical, v1.55.0+ use simplest approach)

**v1.53.0 MCP tool wrapper rejects valid BIP39.** The underlying WalletManager works fine. Bypass the tool:

```python
import os, subprocess

mnemonic = ' '.join(os.environ['AIBTC_MNEMONIC'].strip().split())
password = os.environ['AIBTC_WALLET_PASSWORD'].strip()

script = '''
import { getWalletManager } from "./dist/services/wallet-manager.js";
const wm = getWalletManager();
const result = await wm.importWallet("sonic-mast", process.argv[2], process.argv[3], "mainnet");
console.log(JSON.stringify({ok: true, btc: result.btcAddress}));
'''

with open('/opt/node22/lib/node_modules/@aibtc/mcp-server/import_tmp.mjs', 'w') as f:
    f.write(script)

result = subprocess.run(
    ['node', 'import_tmp.mjs', mnemonic, password],
    capture_output=True, text=True, timeout=30,
    cwd='/opt/node22/lib/node_modules/@aibtc/mcp-server',
    env={**os.environ, 'AIBTC_DIR': os.path.expanduser('~/.aibtc')}
)
print(result.stdout[:200])
os.remove('/opt/node22/lib/node_modules/@aibtc/mcp-server/import_tmp.mjs')
```

After import completes, `wallet_status` MCP tool sees the wallet (reads `~/.aibtc/wallets.json` from disk).

## Step 2 — Unlock wallet via MCP tool

Wallet_unlock works via the session's MCP tool — you just need the literal password value:

```bash
# Read password to pass literally to wallet_unlock
python3 -c "import os; print(os.environ.get('AIBTC_WALLET_PASSWORD',''))"
```

Pass the printed value directly to `mcp__aibtc__wallet_unlock` password parameter.

## Step 3 — Verify BTC address

After unlock, call `wallet_status` — confirm `btcAddress == bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47`.

## Critical: CLIENT_MNEMONIC env does NOT provide BTC keys

Adding `CLIENT_MNEMONIC` to `.mcp.json` env section has two fatal flaws:
1. The env section does NOT expand `${SHELL_VAR}` references — value passed literally.
2. Even if CLIENT_MNEMONIC were a valid mnemonic, `getAccount()` in `x402.service.js` calls `mnemonicToAccount()` which returns **STX keys only** — no BTC keys. `news_file_signal` requires BTC keys for BIP-322 signing. Result: "Bitcoin keys not available".

**Do not use CLIENT_MNEMONIC approach for news_file_signal.** Only the wallet session (import + unlock flow above) provides BTC keys.

## AIBTC_MNEMONIC normalization

The `AIBTC_MNEMONIC` env var has extra internal spaces (161 chars vs expected 157). Always normalize:

```js
const mnemonic = process.env.AIBTC_MNEMONIC.trim().replace(/\s+/g, ' ');
```

Without normalization, `bip39.validateMnemonic` returns false even though the words are correct.

## Fallback: Node.js direct signing (standalone ES module)

If MCP wallet_unlock fails, write a standalone `.mjs` file that imports `@aibtc/mcp-server` internals directly — bypasses the wallet session entirely. Key imports:

```js
import { deriveBitcoinKeyPair } from './dist/utils/bitcoin.js';
import { bip322Sign } from './dist/utils/bip322.js';
import { generateWallet, getStxAddress } from './node_modules/@stacks/wallet-sdk/dist/index.js';
// getStxAddress(account, 'mainnet') — pass string not TransactionVersion enum
// tx.serialize() returns hex string directly — prepend '0x', don't re-encode
```

Place the file inside `/opt/node22/lib/node_modules/@aibtc/mcp-server/` to resolve relative imports. Delete after use.

**How to apply:** In remote sessions: (1) if v1.53.x, import wallet via WalletManager direct (Python subprocess above), (2) for wallet_unlock MCP tool pass literal password read from bash echo, (3) if wallet_unlock MCP fails or news_file_signal needs a wallet, use standalone ES module fallback. The standalone .mjs approach for news_file_signal is confirmed working through to the API call stage on v1.53.0 — failures after that point are API-side (503 identity gate), not signing failures.
