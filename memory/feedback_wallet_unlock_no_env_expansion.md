---
name: feedback_wallet_unlock_no_env_expansion
description: MCP wallet_unlock tool does not expand shell env vars — pass literal password or use Node.js direct decryption for automated runs
metadata:
  type: feedback
  originSessionId: ffa4e9df-eb71-4f89-9506-fd9dcbff0103
---

MCP tool parameters do NOT expand shell variables. Passing `${AIBTC_WALLET_PASSWORD}` to `mcp__aibtc__wallet_unlock` sends the literal string `${AIBTC_WALLET_PASSWORD}`, which fails authentication.

**Why:** Observed 2026-05-20. Automated run attempted `wallet_unlock` with `${AIBTC_WALLET_PASSWORD}` — tool received the unexpanded string and rejected it. The MCP protocol passes parameters as JSON values, not through a shell that would interpolate variables.

**How to apply:** Spawn `aibtc-mcp-server` as a subprocess via Python and communicate over stdio using the MCP JSON-RPC protocol. The env var IS available to the subprocess. Confirmed working 2026-05-21:

```python
import subprocess, json, os
password = os.environ["AIBTC_WALLET_PASSWORD"]
proc = subprocess.Popen(["aibtc-mcp-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL, env={**os.environ, "NETWORK": "mainnet"}, text=True, bufsize=1)
def rpc(proc, msg):
    proc.stdin.write(json.dumps(msg) + "\n"); proc.stdin.flush()
    return json.loads(proc.stdout.readline())
rpc(proc, {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"sonic-mast","version":"1.0"}}})
rpc(proc, {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"wallet_unlock","arguments":{"password":password}}})
result = rpc(proc, {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"news_file_signal","arguments":{...}}})
proc.stdin.close(); proc.terminate()
```

Use this pattern for any wallet-gated MCP call in local automated runs. The subprocess is disposable — no session state leaks. Note: news_file_signal returns 202 (payment queued) which surfaces as an "error" — extract the signalId from the message body. See [[feedback_mcp_no_npx]] for MCP binary config guidance.
