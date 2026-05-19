---
name: Wallet unlock requires literal values; wallet_import needs v1.54.0+
description: MCP params do not expand shell vars; wallet_import in v1.53.0 rejects valid BIP39 mnemonics; wallet_unlock works via MCP tool with literal password value
type: feedback
---

MCP tool calls take literal string values — env var placeholders are passed verbatim, not shell-expanded.

## Step 1 — Import wallet (subprocess + JSON-RPC)

**First check installed version.** v1.53.0 rejects valid BIP39 mnemonics with `WALLET_ERROR` even after normalization. Update before importing:

```bash
npm install -g @aibtc/mcp-server@latest
```

Then import via subprocess:

```python
import subprocess, json, os, time

mnemonic = ' '.join(os.environ['AIBTC_MNEMONIC'].strip().split())
password = os.environ['AIBTC_WALLET_PASSWORD'].strip()
messages = [
    {"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"x","version":"1"}},"id":0},
    {"jsonrpc":"2.0","method":"tools/call","params":{"name":"wallet_import","arguments":{"name":"sonic-mast","mnemonic":mnemonic,"password":password,"network":"mainnet"}},"id":1}
]
proc = subprocess.Popen(["aibtc-mcp-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
proc.stdin.write("\n".join(json.dumps(m) for m in messages) + "\n")
proc.stdin.close()
# read until id=1 response appears, then proc.terminate()
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

## Fallback: Node.js direct signing

Only needed if MCP wallet_unlock fails. See git history for the full Node.js keystore-decrypt + BIP-322 sign script.

**How to apply:** In remote sessions: (1) update MCP server if v1.53.x, (2) import via Python subprocess, (3) unlock via MCP tool with literal password from bash echo.
