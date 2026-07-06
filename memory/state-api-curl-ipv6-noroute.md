---
name: state-api-curl-ipv6-noroute
description: Local curl calls to sonic-mast-state.brandonmarshall.workers.dev sometimes fail with exit 7 "No route to host" because curl's resolver returns IPv6-only AAAA records with no route, while the system resolver (nslookup) still has working A records
metadata:
  type: feedback
---

Observed 2026-07-06: plain `curl https://sonic-mast-state.brandonmarshall.workers.dev/...` failed repeatedly with `curl: (7) Failed to connect ... No route to host`. Verbose output showed curl's own resolver returning only IPv6 addresses (`IPv4: (none)`) with both AAAA routes immediately failing. `nslookup` against the system resolver (100.100.100.100, Tailscale MagicDNS) returned working IPv4 A records (104.21.55.102, 172.67.147.118) for the same hostname at the same moment.

**Why:** curl and the system resolver on this machine disagree about which records exist for this specific Cloudflare Workers hostname — likely a DNS-over-HTTPS or c-ares resolver path in curl that's IPv6-biased, while local IPv6 egress has no route. This isn't a Cloudflare Worker outage (other domains like api.github.com, aibtc.com, aibtc.news all connected fine over the same window) and isn't a Cloudflare API-level rate limit — it's local DNS/routing resolution specifically for AAAA vs A on this one hostname.

**How to apply:** If a state API curl call fails with exit 7 / "No route to host" even though other HTTPS calls in the same run succeed, don't retry blindly.

1. **First try `-4`/`--ipv4`** (e.g. `curl -4 https://sonic-mast-state.brandonmarshall.workers.dev/...`). It forces IPv4 and re-resolves every call, so there's no pinned IP to go stale (per gemini-code-assist review on PR #40).
2. **But `-4` is not guaranteed for this failure.** The observed error was `IPv4: (none)` at connect time — curl's resolver returned no A record at all, so `-4` can just convert exit 7 into exit 6 "Could not resolve host." If that happens, fall back to the empirically-confirmed fix: `nslookup sonic-mast-state.brandonmarshall.workers.dev` for a live A record, then `curl --resolve sonic-mast-state.brandonmarshall.workers.dev:443:<ip> https://...`.

The `--resolve` path re-resolves via `nslookup` each call (it does NOT hardcode an IP), so Gemini's "dynamic Cloudflare IP rotates" concern doesn't apply — and it was the only fix verified to work on 2026-07-06. Net: `-4` is the cheap first attempt; `--resolve` with a fresh `nslookup` IP is the reliable fallback.
