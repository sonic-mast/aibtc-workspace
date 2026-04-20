---
name: arXiv MCP Category Limited
description: arxiv_search only covers cs.AI/cs.CL/cs.LG/cs.MA — useless for Bitcoin/quantum beat research
type: reference
---

`arxiv_search` executes without error but is scoped to AI/ML arXiv categories (cs.AI, cs.CL, cs.LG, cs.MA). It has no free-text query parameter and cannot search Bitcoin cryptography or quantum computing papers.

**Why:** The tool is designed for agent-relevance scoring within AI/ML literature. It is not a general arXiv keyword search engine.

**How to apply:** For quantum beat research, do not call arxiv_search. Use Brave Search (`WebSearch`) with `site:arxiv.org` queries for Bitcoin-cryptography or quantum hardware papers instead. This is the only path to academic paper sourcing for the quantum beat.
