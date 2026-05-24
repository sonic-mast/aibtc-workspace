## User
- [Brandon (operator)](user_brandon.md) — @marshallmixing, technically proficient, prefers terse responses

## Feedback
- [Commit and push promptly](feedback_commit_push.md) — Push cloud-affecting changes immediately after verifying
- [Never fabricate contracts/URLs](feedback_no_fabrication.md) — PR #225 rejected for hallucinated addresses, verify on-chain first
- [Disclosure is separate from body](feedback_disclosure_separate.md) — News signal disclosure field only, never in body text
- [Sync fork before branching](feedback_sync_fork.md) — Stale closed-PR files leak into diff without upstream sync
- [News status vs POST rate limit decoupled](feedback_news_api_status_decoupled.md) — canFileSignal=true doesn't guarantee POST success; handle 429 and cache
- [Outbox field is "reply" not "content"](feedback_outbox_field.md) — POST /api/outbox uses "reply" field, not "content"; prompt template is stale
- [Inbox field names are stale in prompt](feedback_inbox_field_names.md) — Use messageId/fromAddress/peerBtcAddress; not id/senderAddress/senderBtcAddress
- [Quantum governance signals always rejected](feedback_quantum_governance_signals.md) — Only file quantum on hardware milestones, formal BIP stage changes, or arXiv papers; not governance debates
- [Quantum hardware must be shipping, not projected](feedback_quantum_hardware_vs_projection.md) — "X qubits needed to crack Bitcoin" is a projection; only file on actual vendor hardware announcements
- [Twitter-only sources cause rejection](feedback_twitter_source_insufficient.md) — All beats require at least one non-Twitter primary source (GitHub, on-chain tx, API, arxiv/IACR)
- [Quantum Google-derivative rejection](feedback_quantum_google_derivative.md) — Quantum editor blocks Google quantum paper coverage if already filed by another agent; 7-gate + 4-cluster cap applies
- [Cross-agent PR dedup](feedback_cross_agent_dedup.md) — Editors reject signals when another agent already covered the same GitHub PR same day; check all today's signals first
- [bitcoin-macro EDGAR anchor required](feedback_bitcoin_macro_edgar_anchor.md) — Institutional signals score 60-83 with media sources; need SEC EDGAR filing URL as primary to score ≥90
- [CF-1010 ASN block on remote writes](feedback_cf1010_remote_block.md) — Remote runner's ASN blocked by Cloudflare for POST ops to aibtc.com; reads work, writes fail; let local run retry
- [Encourage Discussions participation](feedback_discussions_participation.md) — Sweep aibtcdev/agent-news Discussions each run; reply > post
- [News telemetry lanes score 93-100](news_telemetry_lanes.md) — Structural-telemetry primaries beat SEC 8-K + media; pivot landed in combined.md May 2026
- [aibtc MCP runs binary directly](feedback_mcp_no_npx.md) — .mcp.json calls aibtc-mcp-server directly; npx @latest caused tools-not-registered race in remote sessions
- [Correction dedup across runs](feedback_correction_dedup.md) — Track filed signalIds in `correctionsFiled-YYYY-MM-DD` KV; biggest efficiency drain on the loop
- [pending_payment blocks new signal filings](feedback_pending_payment_blocks_signal.md) — Stuck x402 payment leaves signal in pending_payment; API returns old signalId instead of creating new one
- [Auto-mode blocks wallet unlock in scheduled runs](feedback_automode_wallet_block.md) — Classifier hard-blocks echo of $AIBTC_WALLET_PASSWORD; skip wallet ops, pending signal stays cached

## Projects
- [BFF Skills Competition](project_bff_skills.md) — $100/day, WRITE skills, two-stage PR flow with Devin+Gemini review
- [AIBTC News EIC Pause](project_eic_pause.md) — EIC trial ended 2026-05-07; funding paused; signals queue but no brief payouts until new model
- [BIP-360 is P2MR not P2QRH](feedback_bip360_name.md) — BIP-360 canonical title is Pay-to-Merkle-Root (P2MR); signals calling it P2QRH have a verifiable factual error

## References
- [State API](reference_state_api.md) — Cloudflare Worker KV at sonic-mast-state.brandonmarshall.workers.dev
- [Remote trigger](reference_trigger.md) — aibtc-combined trigger ID, cron, model, tools, MCP connectors
- [News scoring dimensions](news_scoring_dimensions.md) — rejection taxonomy from Apr 2026 probe: Twitter-only 40%, out-of-beat 20%, quantum 7-gate, aibtc-network aibtcdev-scope-only
