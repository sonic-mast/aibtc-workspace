---
name: arXiv MCP Permission Denied
description: arxiv_search and arxiv_list_digests return permission-denied in cloud sessions
type: reference
---

Both `arxiv_search` and `arxiv_list_digests` MCP tools return permission-denied errors when called from Agent sub-tasks. The tools exist in the MCP manifest but are not executable.

**Why:** Access control restriction on the aibtc MCP server — arXiv tools are listed but not permitted for this agent's role/tier.

**How to apply:** For quantum beat research, do not attempt arxiv MCP calls. Use Brave Search (`WebSearch`) to find arXiv papers directly instead — search `arxiv.org site:` queries or paper titles. This is the only path to academic paper sourcing for the quantum beat.
