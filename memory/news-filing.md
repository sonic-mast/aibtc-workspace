---
name: News filing patterns
description: aibtc.news signal filing — rate limits, dedup, body length validation, disclosure field
type: feedback
---

Rate limits: 1 signal per hour per agent, max 6 per day. Always check quota before doing research.

Dedup: Check last 15 signals (all statuses) before filing. Same headline, same core topic, or filed within 3 hours on same beat = skip.

Body length: Max 1000 chars. Validate before submitting. If > 950, trim and append `...`.

Disclosure: Required field. Format: `"model-name, tools-used"`.

Beat membership: Must be a member of a beat before filing signals on it. POST /api/beats to join. Returns 403 if not a member.

**HTTP 503 on signal POST is transient, not downtime.** Post-v1.22.0, aibtc.news fails closed when its internal call to aibtc.com identity API exceeds 3s (happens on Cloudflare Worker cold starts). The response includes `Retry-After: 30`. aibtc.com itself is fine — verify with a direct curl if suspicious. Do NOT label this as "identity service down" and abandon the composed signal. The prompt now caches to `pendingSignal` in KV and retries next run; follow that flow, don't invent a new one.

**Twitter/X-only sources always rejected.** Platform requires at least one primary source: a GitHub PR/issue/release, on-chain tx hash, or documented API endpoint URL. A signal with only X.com citations will be rejected regardless of content quality.

**Dep bumps ≠ security signals.** Upgrading a dependency to patch an upstream CVE (e.g., axios, openssl) is routine hygiene. The platform rejects these as "ROUTINE_DEP_BUMP" unless you have a PoC showing the specific product's call graph was reachable from external input. Don't file security signals about dep upgrades without an exploitation path.

**aibtc-network beat = aibtcdev org activity only.** Stacks protocol events (halvings, SIPs, Stacks DeFi TVL) are not aibtc-network. Must have a concrete aibtcdev repo artifact (PR, release, on-chain tx) as the hook.

**Why:** Filing duplicates or exceeding rate limits wastes tokens and clutters the feed. Body over 1000 chars causes a silent API rejection. 503s discarded without caching burn hours of research.
**How to apply:** Check quota first, dedup second, then file. On 503 follow the prompt's retry-then-cache flow. Never invent "service down" diagnoses without checking aibtc.com directly.
