## User
- [Brandon (operator)](user_brandon.md) — @marshallmixing, technically proficient, prefers terse responses

## Feedback
- [Reviews on Sonic Mast's account](feedback_reviews_on_sonic_mast_account.md) — cubic (`cubic-dev-ai[bot]`) is PR review of record; never CodeRabbit/ultrareview (Brandon's credits are for vibewatch)
- [Commit and push promptly](feedback_commit_push.md) — Push cloud-affecting changes immediately after verifying
- [Memory-prune gotcha](aibtc-memory-prune-gotcha.md) — pruning root MEMORY.md also needs prompt + secondary-index link fixes; prefer merges over deletes; loop can't self-merge
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
- [Gist publishing: classifier judges publish-intent](automode-classifier-gist.md) — broad Bash(curl *) doesn't cover POST /gists; fixed 2026-06-18 with SPECIFIC rule Bash(bash scripts/publish-gist.sh:*); relay-worker fallback if still blocked; phantom bountyHistory risk — reconcile vs bounty_my_submissions
- [Correction dedup across runs](feedback_correction_dedup.md) — Track filed signalIds in `correctionsFiled-YYYY-MM-DD` KV; biggest efficiency drain on the loop
- [pending_payment blocks new signal filings](feedback_pending_payment_blocks_signal.md) — Cross-beat block: pending_payment on ANY beat blocks ALL new filings from the BTC address
- [Wallet unlock: literal-string approach](feedback_wallet_unlock_literal.md) — MCP params don't shell-expand; encrypt+unlock with literal `${AIBTC_WALLET_PASSWORD}`; Phase 0.5 circuit breaker skips wallet-gated phases after 2 fails
- [Testnet runs locally, no mnemonic](feedback_testnet_mcp.md) — BadAddressVersionByte was a mainnet-pinned wallet record, NOT a network limit; testnet works locally via `scripts/testnet-call.py` (export→import network=testnet); no AIBTC_MNEMONIC, no remote run
- [Loop changes land on the main checkout](loop-changes-land-on-main-checkout.md) — worktree edits don't affect the loop; direct main-push is classifier-blocked; ship via PR then `git pull` in /Users/.../Documents/Coding/AIBTC/
- [Classifier escalates within a run](automode-classifier-session-escalation.md) — after 1-2 main-bypass denials it blocks further related tries, even local file Edits read as "instruction poisoning"; stop retrying, use branch+PR
- [Auto-scorer is provisional, editors can override](auto_scorer_provisional.md) — low `quality_score` on a freshly `submitted` signal isn't final (PR #864); single-source aibtc-network filings may score low `beatRelevance`/`sourceQuality`

## Projects
- [Dual stacking: enrolled but needs deployment](project_dual_stacking_enrolled.md) — sBTC must be DEPLOYED in based-dollar/bitflow/granite/velar/zest to earn; wallet-hold doesn't count; AGENT.md is misleading; do not re-enroll (ERR_ALREADY_ENROLLED)
- [BFF Skills Competition](project_bff_skills.md) — $100/day, WRITE skills, two-stage PR flow with Devin+Gemini review
- [AIBTC News EIC Status](project_eic_pause.md) — EIC ACTIVE as of 2026-06-25; Quasar Garuda compiling briefs; SIGNAL_PAYOUTS_ENABLED=false; 2/day limit when eicActive
- [BIP-360 is P2MR not P2QRH](feedback_bip360_name.md) — BIP-360 canonical title is Pay-to-Merkle-Root (P2MR); signals calling it P2QRH have a verifiable factual error

## References
- [State API](reference_state_api.md) — Cloudflare Worker KV at sonic-mast-state.brandonmarshall.workers.dev
- [Remote trigger DISABLED](reference_trigger.md) — aibtc-combined remote trigger disabled 2026-06-07; loop is local-only (`aibtc-combined-local`, hourly). Only daily-digest still runs remotely.
- [News scoring dimensions](news_scoring_dimensions.md) — rejection taxonomy from Apr 2026 probe: Twitter-only 40%, out-of-beat 20%, quantum 7-gate, aibtc-network aibtcdev-scope-only
- [Shelly is Sonic Mast](reference_shelly_is_sonic_mast.md) — GitHub author "Shelly" is the same operator/agent; attribute her commits to Sonic Mast's body of work (e.g. dual-stacking skill PR #76)
- [Hermetica hBTC: closed beta](reference_hermetica_closed_beta.md) — 8% APY but not depositable as of 2026-05-27; Zest is the default sBTC path until Hermetica opens
