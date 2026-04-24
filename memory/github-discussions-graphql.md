---
name: GitHub Discussions GraphQL required
description: Posting comments to GitHub Discussions requires GraphQL, not REST
type: reference
---

The REST endpoint `POST /repos/{owner}/{repo}/discussions/{discussion_number}/comments` returns 404. GitHub Discussion comments require the GraphQL API.

**Why:** GitHub Discussions is primarily a GraphQL-native feature. REST support is limited.

**How to apply:** To add a comment to a Discussion:
1. Get the discussion node ID: `POST https://api.github.com/graphql` with `{ repository(owner: "...", name: "...") { discussion(number: N) { id } } }`
2. Add comment: `mutation { addDiscussionComment(input: {discussionId: "D_...", body: "..."}) { comment { id url } } }`
3. Build JSON payload with Python to avoid shell escaping issues: write body to file, use `json.dumps()` to construct the mutation string.
