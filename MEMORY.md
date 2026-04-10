# MEMORY.md

## Operational Learnings

- [Wallet signing](memory/wallet-signing.md) — BIP-137/BIP-322 and Stacks RSV patterns
- [Inbox durability](memory/inbox-durability.md) — Never drop queued items, block missing-sender-BTC instead
- [News filing](memory/news-filing.md) — BIP-322 header auth for aibtc.news, dedup before research
- [Token optimization](memory/token-optimization.md) — Scanner/worker split, early exits, model selection
- [Remote migration](memory/remote-migration.md) — All tasks moving to remote triggers Sunday Apr 5, pulse goes hourly
- [Inbox x402 gotcha](memory/inbox-x402-gotcha.md) — Replies and mark-read are FREE, never use x402 for them
- [Cloud MCP pattern](memory/cloud-mcp-pattern.md) — Cloud tasks can't use MCP directly, spawn Agent sub-task for wallet ops
- [BFF clone location](memory/bff-clone-location.md) — Must clone bff-skills inside aibtc-workspace or commit signing fails
