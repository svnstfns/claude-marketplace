---
name: truenas-onboarding
description: First-run setup for the TrueNAS connection. Use when test_connection fails, when TRUENAS_HOST/TRUENAS_API_KEY are unset, or when the user says "set up", "connect", "onboard", or "configure" TrueNAS. Guides the user to add their host + API key to the Claude env block — the user does this themselves; the key never passes through the chat.
---

# Onboard a TrueNAS connection

This skill gets the plugin talking to a TrueNAS Scale box. Setup is a
small **manual** step the user performs themselves, because the API key
is a secret that must never pass through the chat/transcript. Your job
is to guide them and verify the result — **not** to receive, request, or
write the key yourself.

## When to use
- `test_connection` returns `connected: false`, or
- `TRUENAS_HOST` / `TRUENAS_API_KEY` are not set, or
- the user explicitly asks to set up / connect / onboard the NAS.

## Hard rule
**Never ask the user to paste their API key into the chat, and never write
it for them.** The user edits their own config file. You only hand them the
steps and then verify.

## Procedure
1. **Check first.** Run `test_connection`. If `connected: true`, tell the
   user they're already set and stop.
2. **Tell the user to create an API key.** In the TrueNAS Scale web UI:
   top-right account menu → **API Keys** (or *Credentials → API Keys*) →
   **Add** → name it → copy the generated key (shown once). Optionally they
   first create a dedicated local user and attach the key to it (least
   privilege).
3. **Tell the user where to put it.** They add (or merge) a top-level `env`
   block in **`~/.claude/settings.json`** (preferred — survives plugin
   updates, every session):
   ```json
   {
     "env": {
       "TRUENAS_HOST": "nas.example.com",
       "TRUENAS_API_KEY": "1-their-key-here",
       "TRUENAS_SSL_VERIFY": "true"
     }
   }
   ```
   Use `"false"` for `TRUENAS_SSL_VERIFY` with a self-signed cert. (Alternative:
   the same `env` values directly in the plugin's `.mcp.json`, replacing the
   `${TRUENAS_*}` placeholders — but that file is overwritten on plugin update,
   so settings.json is preferred.)
4. **Restart.** Claude Code reads `env` at startup, so they must restart
   `claude` for the MCP server to pick up the values.
5. **Verify.** After the restart, run `test_connection` again; confirm
   `connected: true` and report the TrueNAS version. If it fails, it's almost
   always a wrong host, an expired/mistyped key, or a self-signed cert without
   `TRUENAS_SSL_VERIFY=false`.

## What the variables mean
- `TRUENAS_HOST` — NAS hostname or IP (required)
- `TRUENAS_API_KEY` — the API key from the UI (required; secret)
- `TRUENAS_SSL_VERIFY` — `true`, or `false` for self-signed certs (default `true`)
