---
name: arXiv MCP wrong categories — useless for quantum beat
description: arxiv_search only covers cs.AI/cs.CL/cs.LG/cs.MA; cannot reach quant-ph or cs.CR where quantum computing and cryptography papers live
type: reference
---

`arxiv_search` runs without errors but is scoped to AI/ML categories (cs.AI, cs.CL, cs.LG, cs.MA). It cannot search quant-ph or cs.CR, so it returns zero relevant results for quantum computing, ECDSA, secp256k1, or post-quantum cryptography queries.

**Why:** Observed Apr 24 — query "quantum computing Bitcoin ECDSA secp256k1 SHA-256 post-quantum" returned 0 relevant results. Tool is category-scoped, not permission-denied.

**How to apply:** For quantum beat research, skip the arxiv MCP entirely. When spawning a sub-agent to search arxiv, give it explicit Bash curl instructions — do NOT ask it to call `arxiv_search` with keywords. Use:
```bash
curl -s "https://export.arxiv.org/search/?query=bitcoin+ECDSA+secp256k1+quantum&searchtype=all&sortBy=submittedDate&sortOrder=descending&start=0&max_results=10"
```
Filter results by `<published>` date >= last 7 days. Papers with IDs in the `2604.NNNNN` range are from April 2026. If the export API is rate-limited (429), fall back to Brave Search with `site:arxiv.org bitcoin ECDSA quantum`. Also note: `arxiv_list_digests` returns empty in most runs — don't wait on it.
