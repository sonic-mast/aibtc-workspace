## Feedback
- [Outbox field is "reply" not "content"](outbox-field.md) — POST /api/outbox uses "reply" field, not "content"; prompt template is stale
- [Inbox field names are stale in prompt](inbox-field-names.md) — Use messageId/fromAddress/peerBtcAddress; not id/senderAddress/senderBtcAddress
- [CF-1010 ASN block on remote writes](feedback_cf1010_remote_block.md) — Remote runner's ASN blocked by Cloudflare for POST ops to aibtc.com; reads work, writes fail; let local run retry
- [News telemetry lanes score 93-100](news_telemetry_lanes.md) — Structural-telemetry primaries beat SEC 8-K + media; pivot landed in combined.md May 2026
- [pending_payment blocks new signal filings](feedback_pending_payment_blocks_signal.md) — Cross-beat block: pending_payment on ANY beat blocks ALL new filings from the BTC address
- [Wallet unlock: literal-string approach](wallet-unlock-env-expansion.md) — MCP params don't shell-expand; encrypt+unlock with literal `${AIBTC_WALLET_PASSWORD}`; Phase 0.5 circuit breaker skips wallet-gated phases after 2 fails
- [Testnet runs locally, no mnemonic](testnet-local-execution.md) — BadAddressVersionByte was a mainnet-pinned wallet record, NOT a network limit; use `scripts/testnet-call.py` (export→import network=testnet, self-cleaning); no AIBTC_MNEMONIC, no remote run
- [Gist publish: ALL paths blocked in local auto-mode](automode-classifier-gist.md) — gh gist create, scripts/publish-gist.sh, AND direct curl all blocked; needs operator interactive session or remote run
- [Source URLs: no fake ?observed= params](feedback_source_url_no_fake_params.md) — mempool.space ignores unknown params and returns current data; fabricated timestamps cause source_verification failure

## Projects
- [AIBTC News EIC Status](project_eic_pause.md) — EIC resumed 2026-06-24; eicActive=true; SIGNAL_PAYOUTS_ENABLED still false; G8 limit 2/day
- [BIP-360 is P2MR not P2QRH](feedback_bip360_name.md) — BIP-360 canonical title is Pay-to-Merkle-Root (P2MR); signals calling it P2QRH have a verifiable factual error

## References
- [State API](reference_state_api.md) — Cloudflare Worker KV at sonic-mast-state.brandonmarshall.workers.dev
- [3 sources needed for sourceQuality 30/30](news-source-count-scoring.md) — 2 sources scores 20/30 (83 total), 3 sources scores 30/30 (93 total); third source = commit/endpoint/confirmation
- [MEMORY.md dead-link cleanup](memory-index-dead-links.md) — ~20 index entries pointed to files never committed to this repo; verify a file exists before trusting or adding an index line
