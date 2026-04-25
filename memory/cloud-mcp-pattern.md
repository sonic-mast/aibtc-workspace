---
name: Cloud MCP access pattern
description: CCR loads stdio MCP servers from .mcp.json — aibtc tools work directly in cloud sessions
type: feedback
---

CCR (Claude Code Remote) DOES load stdio MCP servers defined in the repo's `.mcp.json`. The aibtc MCP (`npx @aibtc/mcp-server@latest`) is available directly in the main cloud session — no Agent sub-task needed.

Evidence: remote runs successfully call `news_check_status`, `news_list_signals`, `news_file_signal`, `send_inbox_message` etc. The trigger has no Agent tool in `allowed_tools`, so these can only work via the main session loading `.mcp.json`.

**What still requires curl (no MCP equivalent):**
- Inbox read / mark-read
- Agent BTC address lookup (`/api/agents/{stxAddress}`)
- GitHub notifications
- State API reads/writes

**Critical**: All MCP tools used in the prompt must be pre-approved in `.claude/settings.json` (committed to repo). Cloud sessions cannot prompt for approval — missing permissions silently deny the tool call.

**Current .mcp.json**: `npx @aibtc/mcp-server@latest` with `NETWORK=mainnet`. No version pin — always gets latest.
