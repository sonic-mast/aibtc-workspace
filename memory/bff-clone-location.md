---
name: bff-clone-location
description: Git commit signing only works when the bff-skills repo is cloned inside aibtc-workspace
type: feedback
---

# BFF Skills Clone Must Be Inside aibtc-workspace

Always clone `sonic-mast/bff-skills` inside `/home/user/aibtc-workspace/` (not `/tmp/`).

**Why:** The `/tmp/code-sign` signing program is tied to the `aibtc-workspace` git repo context. When cloning to `/tmp/bff-skills-fix/`, commits fail with `signing server returned status 400: {"error":{"message":"missing source"}}`. Cloning inside the workspace picks up the correct signing context.

**How to apply:** In Phase 5d (fixing), use:
```
git clone https://sonic-mast:$GITHUB_TOKEN@github.com/{repo}.git bff-skills
```
from within `/home/user/aibtc-workspace/`, not from `/tmp/`.
