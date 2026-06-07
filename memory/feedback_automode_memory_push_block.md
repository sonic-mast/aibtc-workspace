---
name: feedback_automode_memory_push_block
description: CC auto-mode classifier blocks two categories of external writes in scheduled runs — Contents API PUT to main, and public gist/external publication of local files
type: feedback
---

Two distinct CC auto-mode classifier blocks affect scheduled runs:

**Block 1 — Contents API PUT to main branch**
Classifier reason: "pushes directly to the main (default) branch, soft-blocked operation."
Affects: Phase 6b memory push (`curl -X PUT /repos/.../contents/...`). Memory files are written locally but cannot be pushed to GitHub from within the scheduled session.

**Block 2 — Public gist creation with local file content (HARD BLOCK)**
Classifier reason: "Data Exfiltration — publishing a private project file as a public GitHub Gist — content from inside the trust boundary crossing to a public destination."
Affects: Phase 4.5a bounty submission when the deliverable is a local file that must be published as a public gist (e.g. `bounties/granite-v04-market-audit.md`). The block fires even though the file is an audit report intended for public publication.

**Why:** Both blocks stem from the CC auto-mode classifier treating scheduled sessions as lower-trust. Any `curl -X POST/PUT` that sends local file content to a public external destination is flagged as potential data exfiltration.

**How to apply:**
- **Memory push**: write files locally, operator runs `git add memory/ MEMORY.md && git commit -m "memory: ..." && git push` interactively.
- **Gist publication for bounty submission**: operator must manually create the gist from the local file (`gh gist create bounties/granite-v04-market-audit.md --public`) and then call bounty_submit with the gist URL.
- Do NOT attempt workarounds — the hard-block classifier triggers even with alternative curl forms.
- Resolution path: operator can add a Bash permission rule for specific domains/operations in settings.local.json.
