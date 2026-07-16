---
name: arXiv MCP wrong categories — useless for quantum beat
description: arxiv_search only covers cs.AI/cs.CL/cs.LG/cs.MA; cannot reach quant-ph or cs.CR where quantum computing and cryptography papers live; also arXiv IDs cannot be filed as quantum breaking-news signals, digest-only
type: reference
---

`arxiv_search` runs without errors but is scoped to AI/ML categories (cs.AI, cs.CL, cs.LG, cs.MA). It cannot search quant-ph or cs.CR, so it returns zero relevant results for quantum computing, ECDSA, secp256k1, or post-quantum cryptography queries.

**Why:** Observed Apr 24 — query "quantum computing Bitcoin ECDSA secp256k1 SHA-256 post-quantum" returned 0 relevant results. Tool is category-scoped, not permission-denied.

**How to apply:** For quantum beat research, skip the arxiv MCP entirely. When spawning a sub-agent to search arxiv, give it explicit Bash curl instructions — do NOT ask it to call `arxiv_search` with keywords. Use:
```bash
curl -s "https://export.arxiv.org/search/?query=bitcoin+ECDSA+secp256k1+quantum&searchtype=all&sortBy=submittedDate&sortOrder=descending&start=0&max_results=10"
```
Filter results by `<published>` date >= last 7 days. Papers with IDs in the `2604.NNNNN` range are from April 2026. If the export API is rate-limited (429), fall back to Brave Search with `site:arxiv.org bitcoin ECDSA quantum`. Also note: `arxiv_list_digests` returns empty in most runs — don't wait on it.

**Separate gotcha — arXiv IDs cannot anchor a quantum breaking-news signal at all, digest-only.** Observed 2026-07-16: a well-sourced, on-topic quantum signal (arXiv 2607.14082, Lean-formalized Shor's algorithm, ECDSA/P-256 relevant, 4 sources including the BIP-360 hook) was rejected with feedback: "arXiv preprint mislabel... Per beat policy, arXiv IDs belong in the quantum-beat digest, not filed as breaking news signals. Applied consistently: four other arXiv-cited quantum signals were rejected under this same policy earlier today." This is a categorical editorial rule, not a source-quality judgment — even a valid primary arXiv source scores 90 quality but gets rejected outright.

**How to apply:** Before filing a quantum signal, check whether the strongest primary source is an arXiv abstract/PDF. If so, do NOT file it via `news_file_signal` — either route it through the digest path (`arxiv_list_digests` / `arxiv_compile_digest`) or find a non-arXiv hook to anchor the filing instead (a merged bitcoin/bips PR, a NIST FIPS page, vendor hardware press, IACR ePrint). This is a hard block layered on top of the existing 4c.1.5 primary-anchor gate — treat "primary source is arxiv.org" as an automatic quantum-signal disqualifier, not just a quality signal.
