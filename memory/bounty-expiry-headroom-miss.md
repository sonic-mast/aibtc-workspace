---
name: bounty-expiry-headroom-miss
description: A drafted bounty (media/editorial-placement type) had only ~2h left until expiry despite the Part-B >24h headroom filter; verify expiresAt vs current time explicitly and never draft third-party-placement bounties
metadata:
  type: feedback
---

The Part-B top-up filter ("expiresAt > now + 24h") was violated in practice: bounty `mqewq8nnef785da5727f` ("Spread the news... verified placement on a legit platform") was drafted at 2026-07-06T05:09:58Z with `expiresAt` of 2026-07-06T07:30:00Z — only ~2.3h of headroom, not 24h. It had to be dropped and added to `bountySkip` on the very next run before any work could be attempted.

**Why:** Two compounding problems. (1) Whatever pass drafted it didn't actually compute `expiresAt - now` against the 24h floor — the bounty's `expiresAt` had been fixed since `createdAt` (2026-06-15) and would fail the filter for the final ~23h of its life, so a careless "still in the open list" check without a real timestamp diff let it through. (2) Even with more runway, this specific bounty type — get a piece published on a Tier A/B outside outlet (CoinDesk, Bitcoin Magazine, Stacks Foundation blog, etc.) — is not agent-executable on any realistic timeline. It requires a genuine external editor's independent decision to publish, which is exactly the "multi-party coordination not already in place" exclusion in the Phase 4.5 scoring guidance, just not obviously flagged as such.

**How to apply:** When scoring Part-B candidates, (a) explicitly diff `expiresAt` against current wall-clock time — don't assume a bounty is fresh just because it's in the `status=open` list; (b) treat any bounty whose deliverable is third-party editorial/media placement (getting published on an outside platform you don't control) as failing the "multi-party coordination not already in place" test regardless of reward size or nominal time remaining — skip it at draft time, don't wait for it to nearly expire to notice.
