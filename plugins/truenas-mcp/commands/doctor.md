---
description: Test the TrueNAS connection using the currently configured credentials.
---

Run this command to verify that truenas-mcp can talk to your NAS. It
is read-only — no changes are made on the NAS or in Claude's config.

Via Bash, run:

```
uvx --from git+https://github.com/svnstfns/truenas-mcp.git truenas-mcp doctor
```

Parse the output:

- `OK — version=…` → report success and the TrueNAS version.
- `ERROR: …` → surface the error verbatim. Suggest:
  - If the error mentions "TRUENAS_HOST/API_KEY not set" → tell the
    user to run `/truenas-mcp:install`.
  - Otherwise → suggest the user check the NAS is reachable and the
    API key has not been revoked.
