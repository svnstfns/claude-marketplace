---
description: One-time bootstrap — find your TrueNAS, create a dedicated user, generate an API key, register the MCP server with Claude.
---

This is the first command you should run after installing this plugin.
It sets up everything truenas-mcp needs to talk to your NAS.

Walk the user through the bootstrap.

1. Tell the user this is interactive and asks for their TrueNAS admin
   password. The password MUST NOT be entered into this chat — the
   installer reads it via `getpass` in their own terminal so it never
   lands in the transcript.

2. Print the exact command for them to copy-paste:

   ```
   uvx --from git+https://github.com/svnstfns/truenas-mcp.git truenas-mcp install
   ```

3. Briefly explain the 9 phases they'll see:
   - **Phase 0** — mDNS auto-discovery (5s scan; can skip)
   - **Phase 1** — Hostname (auto-filled from Phase 0 or manual)
   - **Phase 2** — ONE-TIME admin login (username + password, optional 2FA)
   - **Phase 2.5** — Storage pool selection
   - **Phase 3** — Idempotency check (handles existing `claude-llm` user)
   - **Phases 4–6** — Auto: create user, assign privileges, mint API key
   - **Phase 7** — Register with Claude (writes `~/.claude.json`)
   - **Phase 8** — Verify with the new API key

4. Wait for the user to say "done" or similar.

5. Run this via Bash to verify the connection works end-to-end:

   ```
   uvx --from git+https://github.com/svnstfns/truenas-mcp.git truenas-mcp doctor
   ```

   If it prints `OK — version=…`, confirm success.
   If it errors, surface the error and suggest re-running install.

6. Tell them to restart Claude Code so the MCP server in
   `~/.claude.json` loads. After restart, the `truenas-mcp` MCP tools
   become available to skills.
