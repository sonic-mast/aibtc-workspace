# Refresh Reference Files

Runs on Haiku daily. Fetches latest llms.txt and agents.txt files, stores them in the state API, and checks for MCP server updates.

## State API

Store reference files via the state API KV endpoints. Read `STATE_API_TOKEN` from the environment.

- **Write reference**: `curl -s -X PUT "https://sonic-mast-state.brandonmarshall.workers.dev/kv/{key}" -H "Authorization: Bearer $STATE_API_TOKEN" -H "Content-Type: text/plain" -d '{content}'`
- **Check MCP version**: `curl -s "https://sonic-mast-state.brandonmarshall.workers.dev/kv/mcp-pinned-version" -H "Authorization: Bearer $STATE_API_TOKEN"`

## Workflow

Do not narrate. Make tool calls immediately.

### Step 1: Fetch and store reference files

For each source, fetch the URL content and store it in the state API under a `ref:` prefixed key. If a fetch fails (403, 404, timeout), skip it and count as failed.

1. Fetch `https://aibtc.com/llms.txt` → store as key `ref:aibtc.com:llms.txt`
2. Fetch `https://aibtc.com/llms-full.txt` → store as key `ref:aibtc.com:llms-full.txt`
3. Fetch `https://aibtc.news/llms.txt` → store as key `ref:aibtc.news:llms.txt` (may 403 — skip gracefully)
4. Fetch `https://www.bff.army/agents.txt` → store as key `ref:bff.army:agents.txt`

For each fetch, use single-line curl to GET the source, then single-line curl to PUT the content to the state API. Example:
```
content=$(curl -s "https://aibtc.com/llms.txt")
curl -s -X PUT "https://sonic-mast-state.brandonmarshall.workers.dev/kv/ref:aibtc.com:llms.txt" -H "Authorization: Bearer $STATE_API_TOKEN" -H "Content-Type: text/plain" -d "$content"
```

### Step 2: Check for MCP server update

1. Fetch `https://registry.npmjs.org/@aibtc/mcp-server/latest` and read the `version` field.
2. Read current pinned version from state API: `curl -s "https://sonic-mast-state.brandonmarshall.workers.dev/kv/mcp-pinned-version" -H "Authorization: Bearer $STATE_API_TOKEN"`
   - If key doesn't exist (404), store the current version: PUT `1.46.3` to key `mcp-pinned-version`
3. Compare the two versions.
4. If they differ, set `mcpUpdate` to the new version string. Otherwise set `mcpUpdate` to null.

### Output

If no MCP update available:

`Reference Refresh | ok | updated={successCount} | failed={failCount}`

If MCP update available:

`Reference Refresh | ok | updated={successCount} | failed={failCount} | mcp_update_available={newVersion} (pinned={currentVersion})`

## Rules

- No wallet unlock needed. No signing needed. Read-only fetches + state writes.
- Do NOT auto-update the pinned version. Just report that an update is available.
- On total failure (all fetches fail and npm check fails), end with:
  `Reference Refresh | error | all fetches failed`
- No markdown, no bullets, no code fences in final response.
