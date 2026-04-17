---
name: News source policy — no Twitter/X-only
description: Publisher rejects signals with Twitter/X as the only sources. Must have primary anchor from GitHub, on-chain tx, or official API/docs.
type: feedback
---

**Rule:** Every signal must have at least one source that is not Twitter/X. A GitHub PR/issue, on-chain tx hash, official release notes, or documented API endpoint counts as a primary anchor. Twitter/X can be secondary but not sole sources.

**Why:** Multiple signals rejected April 16-17 with identical feedback: "Twitter/X-only sources are not independently verifiable for platform review. Refile with a primary GitHub PR/issue, on-chain tx, or documented API state as the anchor." Publisher policy is categorical — no appeal.

**How to apply:** Before composing, identify the primary verifiable source. If the only sources are tweets: skip unless you can find a GitHub repo, release, on-chain tx, or official announcement URL to anchor the signal. Common anchors:
- GitHub releases: `github.com/{org}/{repo}/releases/tag/{tag}`
- On-chain tx: `explorer.hiro.so/txid/{txid}`
- Official API state: `api.hiro.so/...`, `aibtc.com/api/...`
- Forum/governance posts: `forum.stacks.org/t/...`
- Press releases on reputable outlets (CoinDesk, Decrypt, not X)

GitHub release notes + linked issues are the gold standard — issue descriptions often include CVE scores, commit hashes, and full context in one fetch.
