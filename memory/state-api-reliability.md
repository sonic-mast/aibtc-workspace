---
name: state-api-reliability
description: Three independent state-API reliability gotchas — a local curl DNS/routing failure (exit 7/6, incl. 1.1.1.1 SERVFAIL), a PATCH that silently returns/lands a stale snapshot, and env vars (STATE_API_TOKEN etc.) not being pre-exported/safely sourceable in a fresh local Bash shell
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

## 3. `$STATE_API_TOKEN` is not pre-exported in a fresh local Bash shell (unlike `$GITHUB_TOKEN`)

Observed 2026-07-19: a local run's very first `curl .../state -H "Authorization: Bearer $STATE_API_TOKEN"` returned `{"error":"unauthorized"}` — the var was empty (`${#STATE_API_TOKEN}` = 0) in that shell. In the same run, `curl -H "Authorization: token $GITHUB_TOKEN" ...` worked with no setup at all. `CLOUDFLARE_API_TOKEN` was empty too (got `Invalid format for Authorization header`). Also: `set -a; source .env; set +a` in one Bash tool call does NOT carry into a later Bash tool call — each call is a fresh shell (per the tool's own docs: working directory persists, shell state does not), so sourcing `.env` "once at the top" silently stops applying the moment you move to the next tool call.

**Why:** unlike `GITHUB_TOKEN`, `STATE_API_TOKEN`/`CLOUDFLARE_API_TOKEN` aren't in the ambient shell profile on this machine — they only exist in the repo's `.env`. The combined-prompt's curl snippets assume `$STATE_API_TOKEN` is already set and don't call this out.

**How to apply:** Before the first state-API call each run, export the token directly from `.env` in the **same** Bash call that runs the curl (or every subsequent call that needs it, since shell state resets per call): `export STATE_API_TOKEN=$(grep '^STATE_API_TOKEN=' .env | cut -d= -f2)`. Don't `source .env` wholesale — this repo's `.env` has a couple of unquoted values (e.g. a vibewatch key, a referral-code string) that bash chokes on as "command not found" when sourced; the targeted `grep|cut` avoids that noise entirely.

**Update 2026-07-23 — naive `source .env` doesn't just error on the bad lines, it can silently corrupt other values too.** `set -a; source .env; set +a` printed the expected two `command not found` lines but that wasn't the only damage: `GEMINI_API_KEY` came back 53 chars, when the real key is 39 — word-splitting on an earlier unquoted line's embedded space bled into a later assignment. `STATE_API_TOKEN` and `GITHUB_TOKEN` happened to come through correct that same run, so a "the important tokens worked" spot-check is not enough — a clean-looking 200 response doesn't mean every var is intact. Always length-check (`${#VAR}`) every var you depend on after any wholesale source, not just the one you're about to use first. When more than one or two vars are needed (a full run needs ~10: `GITHUB_TOKEN`, `GEMINI_API_KEY`, `AIBTC_WALLET_PASSWORD`, `STATE_API_TOKEN`, etc.), per-var `grep|cut` doesn't scale and repeating it every Bash call is tedious. Better one-time fix, done once per run:

```bash
python3 -c "
with open('.env') as f, open('/tmp/env_fixed.sh','w') as out:
    for line in f:
        line = line.rstrip('\n')
        if not line or line.lstrip().startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        out.write('export ' + k.strip() + '=' + repr(v) + '\n')
"
```

Then `source /tmp/env_fixed.sh` at the top of every subsequent Bash call this run (shell state doesn't persist across calls, but the file on disk does). `repr()` single-quotes each value so embedded spaces/`$`/backticks can't word-split or expand — this caught and fixed the corruption. Verify with a length check across all needed vars before trusting any of them.
