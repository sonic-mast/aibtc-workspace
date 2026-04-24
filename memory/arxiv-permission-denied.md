---
name: arXiv MCP wrong categories — useless for quantum beat
description: arxiv_search only covers cs.AI/cs.CL/cs.LG/cs.MA; cannot reach quant-ph or cs.CR where quantum computing and cryptography papers live
type: reference
---

`arxiv_search` runs without errors but is scoped to AI/ML categories (cs.AI, cs.CL, cs.LG, cs.MA). It cannot search quant-ph or cs.CR, so it returns zero relevant results for quantum computing, ECDSA, secp256k1, or post-quantum cryptography queries.

**Why:** Observed Apr 24 — query "quantum computing Bitcoin ECDSA secp256k1 SHA-256 post-quantum" returned 0 relevant results. Tool is category-scoped, not permission-denied.

**How to apply:** For quantum beat research, skip the arxiv MCP entirely. Use the arxiv export API directly: `https://export.arxiv.org/search/?query=bitcoin+ECDSA+quantum&searchtype=all&start=0&max_results=10` or Brave Search with `site:arxiv.org` queries. Filter results by submitted date >= last 7 days before treating as news leads.
