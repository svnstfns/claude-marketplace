---
description: Remove the dedicated service user, privilege, and API key from your NAS. Reverses /truenas-mcp:install.
---

⚠️ This is destructive on the NAS side — it deletes the `claude-llm`
service user, its privilege binding, and the API key. Your apps and
data on the NAS are NOT touched.

Walk the user through teardown.

1. Ask the user to confirm they really want to uninstall. If they
   waver, list what will be removed and what will remain (their apps,
   pools, shares are all untouched).

2. Print the exact command:

   ```
   uvx --from git+https://github.com/svnstfns/truenas-mcp.git truenas-mcp uninstall
   ```

3. Remind them they need the TrueNAS admin password one more time
   (same reason as `install` — destructive operations need
   re-authentication).

4. Wait for "done".

5. Via Bash, run `uvx --from git+... truenas-mcp doctor`. It should
   now error (no API key configured, or key rejected). Report this as
   expected.

6. If the user also wants to remove the plugin itself from Claude,
   tell them to run:

   ```
   claude plugin uninstall truenas-mcp
   ```
