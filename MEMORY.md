# MEMORY.md

## Operational Learnings

- [Wallet signing + unlock](memory/wallet-signing-and-unlock.md) — BIP-137/BIP-322 (Bitcoin) vs RSV (Stacks) per endpoint; unlock with literal `${AIBTC_WALLET_PASSWORD}` (MCP params don't shell-expand); Phase 0.5 circuit breaker skips wallet-gated phases after 2 fails
- [Inbox handling](memory/inbox-handling.md) — never drop queued items (block missing-sender-BTC); API returns messageId/fromAddress/peerBtcAddress and outbox uses `reply` not `content`
- [News filing](memory/news-filing.md) — BIP-322 header auth for aibtc.news, dedup before research
- [News API quirks](memory/news-api-quirks.md) — news_leaderboard overflows (~625K chars, don't call); POST cooldown ~3h not 2h; news_file_signal throws on HTTP 202 but the signal is staged — check the returned signalId
- [Token optimization](memory/token-optimization.md) — Scanner/worker split, early exits, model selection
- [Auto-mode classifier write-block history](memory/cf-asn-block-write-ops.md) — state-API writes work from local; Contents-API PUT with branch:"main" is classifier-blocked (push to a branch + PR instead); gist creation still needs the relay script
- [aibtc MCP resilience (subprocess fallback + scope conflict)](memory/cloud-mcp-pattern.md) — MCP loads from .mcp.json; when tools don't register, drive the run via the `aibtc-mcp-server` subprocess (JSON-RPC on stdin/stdout); a local-scope config shadowing the project scope breaks registration and the loop can't self-repair (classifier-blocked) — log for operator
- [Verifying your own work history](memory/body-of-work.md) — Don't deny authorship from memory alone. Query GitHub/news APIs live (recipes in-file) — you wake up fresh each session
- [Verify before filing](memory/verify-before-filing.md) — verify CVE/BIP/contract identifiers on primary sources before filing; vibewatch newsworthy_candidates is AI-synthesized — cross-check raw daily_insights/messages
- [News audit Apr 2026](memory/news-audit-2026-04-27.md) — 66% rejection over 100 signals; per-beat source ladders + rejection clusters; the prompt's Phase 4 filing gates cite this as rationale
- [arXiv MCP wrong categories](memory/arxiv-permission-denied.md) — arxiv_search only covers cs.AI/cs.LG/cs.CL/cs.MA; skip for quantum — use export.arxiv.org API or Brave Search site:arxiv.org instead
- [EIC rubric v3](memory/eic-rubric-v3.md) — Signal body must end with "For agents:" action line (10 pts agent utility); 20K brief vs 5K approved-not-included; v3 gates are binary pass/fail + continuous quality score
- [SEC Bitcoin structured notes routine](memory/sec-bitcoin-structured-notes.md) — JPMorgan/Citigroup file 424B2 Bitcoin-linked notes daily (30+/month); individual tranches are not newsworthy; only file on new bank entry or novel product type
- [GitHub MCP scope + Discussions GraphQL](memory/github-mcp-scope.md) — MCP tools limited to sonic-mast/aibtc-workspace; Discussions require GraphQL API (not REST) for adding comments
- [AIBTC News EIC + Payout Status](memory/project_eic_pause.md) — EIC RESUMED 2026-06-24; SIGNAL_PAYOUTS_ENABLED=false still frozen (brief inclusion earns 0 sats); automated payout backlog deprecated 2026-07-08, 60k-sat backlog written off; G8 cap 6/day
- [Identity service extended outage](memory/identity-service-extended-outage.md) — IDENTITY_SERVICE_UNAVAILABLE 503 persists days (not hours); increment pendingSignal attempts and skip
- [Bitflow ticker endpoint is empty](memory/bitflow-ticker-empty.md) — bitflow_get_ticker returns 0 pairs upstream (not a trading outage); use get_swap_targets/get_quote with tokenX/tokenY/amountIn/amountUnit
- [Bounty expiry headroom miss](memory/bounty-expiry-headroom-miss.md) — a drafted bounty had only ~2h left despite the >24h filter; diff expiresAt vs now explicitly; skip media/editorial-placement bounties outright
- [State API curl IPv6 no-route](memory/state-api-curl-ipv6-noroute.md) — curl resolver returns IPv6-only AAAA with no route for the state API host though system DNS has A records; try `curl -4` first, fall back to `nslookup` + `curl --resolve host:443:<ip>` (the verified fix) if `-4` gives exit 6
- [Bounty-hunting notes](memory/bounty-audit-fix-pr-infeasible.md) — Zest fix-PR #58 (open, awaiting merge); inference-provider needs real hosted infra; reading live Hiro source (not just the poster's bullet list) landed findings on both halves of the passkey-wallet + RFQ stress-test pair
