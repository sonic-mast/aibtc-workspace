---
name: Wallet unlock requires literal password value
description: MCP tool parameters don't expand shell env vars; must read AIBTC_WALLET_PASSWORD via bash first
type: feedback
---

MCP tool calls (e.g. `wallet_unlock`) take literal string values — `${AIBTC_WALLET_PASSWORD}` as a parameter is passed verbatim, not shell-expanded. Always read the env var value via bash first:

```bash
PW=$(python3 -c "import os; print(os.environ.get('AIBTC_WALLET_PASSWORD',''))")
```

Then pass `$PW` (or the value inline) to the tool.

**Why:** Two failed unlock attempts per session wastes tokens and risks stalling wallet-gated phases.
**How to apply:** Before every wallet_unlock call, retrieve the actual password string from the shell environment, not the variable placeholder.
