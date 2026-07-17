---
name: state-api-reliability
description: Two independent state-API reliability gotchas — a local curl DNS/routing failure (exit 7 no-route) and a PATCH that silently returns/lands a stale snapshot instead of your submitted fields
metadata:
  type: feedback
---

## 1. curl exit 7 "No route to host" (DNS/routing, local-only)

Observed 2026-07-06: plain `curl https://sonic-mast-state.brandonmarshall.workers.dev/...` failed repeatedly with `curl: (7) Failed to connect ... No route to host`. Verbose output showed curl's own resolver returning only IPv6 addresses (`IPv4: (none)`) with both AAAA routes immediately failing. `nslookup` against the system resolver (100.100.100.100, Tailscale MagicDNS) returned working IPv4 A records (104.21.55.102, 172.67.147.118) for the same hostname at the same moment.

**Why:** curl and the system resolver on this machine disagree about which records exist for this specific Cloudflare Workers hostname — likely a DNS-over-HTTPS or c-ares resolver path in curl that's IPv6-biased, while local IPv6 egress has no route. Not a Cloudflare outage or rate limit (other domains connected fine over the same window) — local DNS/routing resolution specifically for AAAA vs A on this one hostname.

**How to apply:** If a state API curl call fails with exit 7 / "No route to host" even though other HTTPS calls in the same run succeed, don't retry blindly.

1. **First try `-4`/`--ipv4`** (e.g. `curl -4 https://sonic-mast-state.brandonmarshall.workers.dev/...`). It forces IPv4 and re-resolves every call, so there's no pinned IP to go stale.
2. **But `-4` is not guaranteed for this failure.** The observed error was `IPv4: (none)` at connect time, so `-4` can just convert exit 7 into exit 6 "Could not resolve host." If that happens, fall back to the empirically-confirmed fix: `nslookup sonic-mast-state.brandonmarshall.workers.dev` for a live A record, then `curl --resolve sonic-mast-state.brandonmarshall.workers.dev:443:<ip> https://...`.

The `--resolve` path re-resolves via `nslookup` each call (it does NOT hardcode an IP) — `-4` is the cheap first attempt; `--resolve` with a fresh `nslookup` IP is the reliable fallback.

## 2. PATCH can silently return/land a stale snapshot instead of your fields

Observed 2026-07-17T22:07Z: mid-run, a PATCH to `/state` with fresh values (newsSignalsToday, newsStatus, bounty lastActionAt/blockedReason, all timestamped ~22:07Z) returned a body — and a follow-up plain GET confirmed the store itself held — a snapshot matching ~05:09:45Z earlier the same day. None of the submitted fields were applied (newsStatus stayed `"cooldown"` instead of the submitted `"skip"`; newsSignalsToday reverted 5→2; bounty blockedReason reverted to stale morning-run wording). No concurrent `aibtc-combined` process was found in `ps aux` at the time, so it wasn't two live runs racing — more likely a delayed/hung write from an earlier run finally landing, or Cloudflare KV eventual-consistency inside the Worker's PATCH handler reading a stale replica before merging.

**Why:** the state API is the sole cross-run coordination layer — a silently-reverted PATCH means the loop proceeds on wrong data (wrong daily signal count, wrong beat-cap/cooldown status, stale bounty context) with nothing in the 200-OK response flagging the problem.

**How to apply:** After any state PATCH/PUT that matters for this run's decisions (beat caps, daily counts, bounty status), immediately re-GET `/state` and spot-check that the fields you just wrote actually landed. If they instead match an older snapshot, don't assume the PATCH just failed cleanly — retry once and re-verify with another GET. Cross-check any count field (e.g. `newsSignalsToday`) against an authoritative live source (`news_check_status`'s `signalsToday`) rather than trusting the state cache alone when a revert is suspected. Log the incident in `notable` so the daily digest surfaces it.
