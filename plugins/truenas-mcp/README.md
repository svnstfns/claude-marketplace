# truenas-mcp

Deploy and manage TrueNAS Scale (≥ 25.04) Docker apps from Claude Code.

## First-Time Setup

After `claude plugin install truenas-mcp`:

1. ✓ Plugin installed (you're here).
2. → Run `/truenas-mcp:install` in any Claude Code session.
   The command walks you through finding your NAS on the local
   network, creating a dedicated service user (`claude-llm`),
   and generating an API key. Your admin password is entered
   in your own terminal — never in the Claude chat.
3. → Restart Claude Code so the MCP server loads. The
   `truenas-mcp` tools become available to skills.

To verify the setup at any time, run `/truenas-mcp:doctor`. To tear
it down, run `/truenas-mcp:uninstall`.

The bootstrap is idempotent: re-running install on an existing
`claude-llm` user offers to either reuse it (just mint a new API
key) or recreate it from scratch.

## About the plugin

This plugin bundles the procedural knowledge (skills) and slash commands that drive the [`truenas-mcp`](https://github.com/svnstfns/truenas-mcp) MCP server. The server itself is fetched at runtime by `uvx` straight from its git repository — no separate install needed.

## What you get

**Skills** (LLM consults them when the task matches their description):

| Skill | Used for |
|---|---|
| `truenas-discovery` | Read-only inventory of pools, networks, apps before any deploy decision |
| `truenas-deployment-planning` | Pick network model, storage layout, auth layer, hardening — before any compose is built |
| `truenas-deploy-and-verify` | Validate → deploy → verify pipeline with structured failure diagnosis |
| `truenas-troubleshoot` | Diagnose broken / stuck / unhealthy apps from logs and state |
| `truenas-purge-failed` | Destructive cleanup of failed or abandoned apps (with confirmation) |

**Slash commands:**

| Command | Purpose |
|---|---|
| `/truenas-list [state]` | List apps, optionally filter by `running` / `stopped` / `error` / `deploying` |
| `/truenas-status` | Compact dashboard — system + pools + apps grouped by state |

**MCP server (auto-registered):** `truenas` (stdio, 15 tools — `test_connection`, `list_apps`, `deploy_app`, `verify_deployment`, `purge_app`, `validate_compose`, `get_app_details`, `get_app_logs`, `get_docker_networks`, `get_system_info`, …)

## Install

```bash
# One-time — add the marketplace
claude plugin marketplace add https://github.com/svnstfns/claude-marketplace

# Install the plugin
claude plugin install truenas-mcp
```

## Configure

The MCP server reads its connection settings from environment variables. Set these in your shell or in `~/.config/claude-code/env` before triggering any TrueNAS skill:

| Variable | Meaning | Default |
|---|---|---|
| `TRUENAS_HOST` | TrueNAS Scale host (`nas.example.com` or IP) | required |
| `TRUENAS_API_KEY` | API key from the TrueNAS UI (Settings → API Keys) | required |
| `TRUENAS_SSL_VERIFY` | `true` to verify TLS cert, `false` for self-signed | `true` |
| `MOCK_TRUENAS` | `true` runs the server against an in-memory mock (no NAS needed) | `false` |

The skills will surface a clear error if `test_connection` fails — most often this means a bad host, expired key, or self-signed cert without `TRUENAS_SSL_VERIFY=false`.

## How the skills compose

```
truenas-discovery       ──►  truenas-deployment-planning  ──►  truenas-deploy-and-verify
   (read-only,                  (architecture decisions,           (validate → deploy →
    NAS profile)                 no deploy)                         verify → diagnose)

                              truenas-troubleshoot                 truenas-purge-failed
                              (diagnose only)                      (destructive cleanup)
```

A typical session: the user says "deploy Paperless on the NAS". Discovery runs first, surfaces facts and assumptions, the user confirms. Planning then walks the five core decisions (reverse proxy, NIC binding, per-app IP, storage, NAS UI exposure) plus any conditional decisions (backend split, auth layer, socket exposition, build caching), runs the hardening veto, and hands off a finished compose. Deploy-and-verify executes it.

## Source

- Server source + issues: [github.com/svnstfns/truenas-mcp](https://github.com/svnstfns/truenas-mcp)
- This plugin's source (skills + commands + manifest): [`plugins/truenas-mcp/`](.) in this marketplace

## Versioning

The plugin version (`0.1.0`) is independent of the server version. The MCP entry pulls the server from the default branch of the source repository — pin to a tag by editing `.mcp.json` if you need a reproducible runtime build (`git+https://github.com/svnstfns/truenas-mcp.git@v0.2.0`).

## License

MIT — see [LICENSE](../../LICENSE) at the marketplace root.
