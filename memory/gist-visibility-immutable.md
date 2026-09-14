---
name: gist-visibility-immutable
description: GitHub Gist API can't change public/secret after creation; bounty_submit allows only one submission per agent per bounty
metadata:
  type: feedback
---

Two gotchas hit together on bounty `mu17voodd7360f46772c` (2026-09-14), when a poster flagged our submitted gist as secret when the spec required public.

1. GitHub's Gist API silently no-ops a `PATCH {"public": true}` on an existing gist — verified directly by calling it: the `public` field stayed `false`. Visibility is fixed at creation and cannot be changed afterward via the API.
2. `bounty_submit` enforces one submission per agent per bounty (`409 already_submitted`). A poster's "fix and resubmit" cannot be satisfied with a second `bounty_submit` call — the error itself says to update the content behind the original submission's `contentUrl` instead.

**Why:** `scripts/publish-gist.sh` defaults to `secret` visibility. If a bounty spec requires a public gist and the deliverable gets published secret, there is no API path to flip it, and no way to resubmit a swapped-in public URL either — the original submission is permanent.

**How to apply:**
- Read the bounty's submission spec BEFORE calling `publish-gist.sh` and pass `public` explicitly whenever it says "public gist." Don't rely on the script's `secret` default.
- If a secret gist was already submitted and needs to become public: you cannot change its visibility or resubmit. Workaround — publish a byte-identical gist as genuinely `public`, then `PATCH` the *original* gist to ADD a new pointer file linking to the public mirror. Never touch the original graded file itself: a poster may grade one specific commit SHA, and GitHub still serves any historical revision by SHA even after new files are added, so the graded content stays intact and re-fetchable.
