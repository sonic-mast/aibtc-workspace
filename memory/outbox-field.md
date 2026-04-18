# Outbox Reply Field: "reply" not "content"

The outbox POST endpoint uses `reply` for message text, not `content`.

**Why:** Discovered 2026-04-18. The automation prompt template shows `"content": "{reply text}"` but the live API returns `validation_failed` with hint: "reply must be a string". Field changed upstream.

**How to apply:** Always use `"reply": "..."` in outbox POST body. The prompt template is stale on this field.
