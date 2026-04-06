---
name: Remote migration — completed
description: Architecture finalized. Heartbeat on Cloudflare Worker, inbox+news on Claude Code cloud trigger.
type: project
---

## Final Architecture (Apr 6, 2026)

| Component | Where | Schedule | Cost |
|---|---|---|---|
| Heartbeat | Cloudflare Worker (`sonic-mast-heartbeat`) | */15 * * * * | $0 |
| Inbox + News | Claude Code cloud trigger (`aibtc-combined`) | hourly | ~19% weekly Max budget |
| Reference refresh | local desktop task | daily | minimal |
| State API | Cloudflare Worker (`sonic-mast-state`) + KV | always on | $0 |

## Key Learnings

- Max plan allows only 1 hourly cloud trigger — had to combine all AI tasks into one session
- Cloud sessions can't use MCP tools directly — spawn Agent sub-tasks for wallet operations
- `.claude/settings.json` (committed) provides permissions for cloud sessions
- `.claude/settings.local.json` (gitignored) is for local-only permissions
- Setup script: `npm install -g @aibtc/mcp-server@1.46.3 && echo '{"mcpServers":...}' > .mcp.json`
- Heartbeat doesn't need AI — pure crypto worker, runs free on Cloudflare
- Token optimization: pipe API responses through python to extract only needed fields before Claude sees them
- Quiet runs cost ~500 tokens. Active runs cost ~15-25K tokens.

## Cloudflare Resources

- State Worker: `sonic-mast-state.brandonmarshall.workers.dev` (KV: `bee217d801e44978a1297c19d10db914`)
- Heartbeat Worker: `sonic-mast-heartbeat.brandonmarshall.workers.dev` (cron: */15)
- Account: `7a4f8f49f0affd90960dfcaac7ba248b`

## Repo

`https://github.com/sonic-mast/aibtc-workspace`
