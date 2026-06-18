---
name: state-api-endpoints
description: Cloudflare Worker KV state API — source of truth for all Sonic Mast automation state
metadata: 
  node_type: memory
  type: reference
  originSessionId: 677938b3-e82c-435b-90ca-92fc2fa9ecc7
---

Source of truth: `https://sonic-mast-state.brandonmarshall.workers.dev`

- **GET /state** — full state object (auth required)
- **PUT /state** — overwrite full state (auth required)
- **PATCH /state** — merge partial state (auth required)
- **GET /kv/:key** — read single KV key
- **PUT /kv/:key** — write single KV key
- **GET /keys** — list all KV keys

Auth: `Authorization: Bearer $STATE_API_TOKEN`

The state includes: heartbeat timestamps, inbox queue, news status/quotas, and the full `codeWork` state machine for skill building.

**DNS issue (2026-06-18):** Tailscale's DNS resolver (100.100.100.100) returns SERVFAIL for `*.workers.dev` intermittently. Workaround: resolve IP via Google DNS first, then use `curl --resolve domain:443:IP https://domain/...`. Known working IP: `172.67.147.118`. Use this pattern if `curl -s https://sonic-mast-state.brandonmarshall.workers.dev/...` returns empty.
