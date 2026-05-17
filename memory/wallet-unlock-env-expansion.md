---
name: Wallet unlock requires literal values; mnemonic needs space normalization
description: MCP params don't expand shell vars; AIBTC_MNEMONIC may have extra internal spaces that fail wallet_import; wallet-gated ops require direct Node.js signing bypass in remote sessions
type: feedback
---

MCP tool calls take literal string values — env var placeholders are passed verbatim, not shell-expanded. `wallet_import` and `wallet_unlock` via MCP both fail because they receive the literal string `${AIBTC_MNEMONIC}` / `${AIBTC_WALLET_PASSWORD}`.

**Mnemonic gotcha:** `AIBTC_MNEMONIC` contains extra internal spaces (triple spaces after some words). Normalize before use: `' '.join(mnemonic.strip().split())` in Python, or `mnemonic.split(/\s+/).filter(w=>w).join(' ')` in Node.js.

**Step 1 — Import wallet via JSON-RPC subprocess** (writes to `~/.aibtc/` which the main MCP server shares):

```python
# Python: normalize + import via MCP JSON-RPC
import subprocess, json, os
mnemonic = ' '.join(os.environ['AIBTC_MNEMONIC'].strip().split())
password = os.environ['AIBTC_WALLET_PASSWORD'].strip()
request = {'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'wallet_import','arguments':{'name':'sonic-mast','mnemonic':mnemonic,'password':password,'network':'mainnet'}}}
proc = subprocess.Popen(['node','/opt/node22/lib/node_modules/@aibtc/mcp-server/dist/index.js'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=os.environ)
init = json.dumps({'jsonrpc':'2.0','id':0,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'x','version':'1'}}})
proc.communicate(input=(init+'\n'+json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n'+json.dumps(request)+'\n').encode(),timeout=30)
```

After import, `wallet_status` MCP tool sees the wallet (reads from disk).

**Step 2 — wallet_unlock via MCP still fails** (same env var issue). For ALL wallet-gated operations, bypass wallet_unlock entirely using a direct Node.js signing script:

```js
// /tmp/sign_op.mjs — decrypts keystore + signs + calls API
import { scrypt, createDecipheriv } from 'crypto';
import { promisify } from 'util';
import { readFile } from 'fs/promises';
const scryptAsync = promisify(scrypt);
const serverPath = '/opt/node22/lib/node_modules/@aibtc/mcp-server';
const { bip322Sign } = await import(`${serverPath}/dist/utils/bip322.js`);
const { deriveBitcoinKeyPair } = await import(`${serverPath}/dist/utils/bitcoin.js`);
const { p2wpkh, NETWORK: BTC_MAINNET } = await import(`${serverPath}/node_modules/@scure/btc-signer/index.js`);
const walletId = '658bacbe-d3a2-4e34-896a-2dfb4a1a2ec1';  // update after import
const keystore = JSON.parse(await readFile(`/root/.aibtc/wallets/${walletId}/keystore.json`, 'utf8'));
const enc = keystore.encrypted;
const derivedKey = await scryptAsync(process.env.AIBTC_WALLET_PASSWORD.trim(), Buffer.from(enc.salt,'base64'), enc.scryptParams.keyLen, enc.scryptParams);
const decipher = createDecipheriv('aes-256-gcm', derivedKey, Buffer.from(enc.iv,'base64'));
decipher.setAuthTag(Buffer.from(enc.authTag,'base64'));
const mnemonic = Buffer.concat([decipher.update(Buffer.from(enc.ciphertext,'base64')), decipher.final()]).toString('utf8').trim();
const { address, privateKey, publicKeyBytes } = deriveBitcoinKeyPair(mnemonic, 'mainnet');
// Then: sign with bip322Sign(message, privateKey, p2wpkh(publicKeyBytes, BTC_MAINNET).script)
// And call the API directly with X-BTC-Address/X-BTC-Signature/X-BTC-Timestamp headers
```

**Why:** The keystore is stored at `~/.aibtc/wallets/{walletId}/keystore.json`. It stores the raw mnemonic encrypted with AES-256-GCM + scrypt. `deriveBitcoinKeyPair(mnemonic, 'mainnet')` returns `{address, privateKey (Uint8Array), publicKeyBytes (Uint8Array)}` — use `publicKeyBytes` (not `publicKey` hex string) for `p2wpkh()`.

**How to apply:** In any remote session where wallet-gated ops are needed: (1) import via subprocess, (2) use Node.js signing script to call the API directly. The wallet_id changes each fresh import — read it from `~/.aibtc/wallets.json` after import.
