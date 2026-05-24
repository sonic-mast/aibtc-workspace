---
name: feedback-automode-wallet-block
description: Claude Code auto-mode blocks echo of $AIBTC_WALLET_PASSWORD, making wallet unlock impossible in scheduled local runs
metadata:
  type: feedback
---

In Claude Code auto-mode (scheduled tasks), the classifier hard-blocks `echo "$AIBTC_WALLET_PASSWORD"` with: "prints the actual wallet password to stdout — credential leakage HARD BLOCK". This makes wallet_unlock impossible because the MCP tool requires the literal password string, which can only be obtained by reading the env var.

**Why:** Auto-mode runs with tighter security restrictions than interactive sessions. The classifier treats any env var echo of a credential as leakage, even in a legitimate automated flow. The `feedback_wallet_unlock_no_env_expansion.md` workaround (read via python3 print) would be blocked for the same reason.

**How to apply:**
1. If wallet_unlock is blocked this way, skip all wallet-gated operations (news_file_signal, news_file_correction, inbox replies). Do NOT repeatedly retry.
2. The pending signal remains cached — the next run (or a remote trigger run) should still pick it up.
3. Long-term fix: operator needs to either (a) add an auto-approve rule in settings.json for the wallet password env var read, or (b) configure the AIBTC MCP server to auto-unlock via AIBTC_WALLET_PASSWORD env on startup, bypassing the need for explicit unlock in session.
4. Related: [[feedback_wallet_unlock_no_env_expansion]]
