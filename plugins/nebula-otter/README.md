# nebula-otter

Manage Docker apps on **TrueNAS SCALE 25.04** from Claude Code.

## What it does

Provides a complete workflow for deploying, managing, and troubleshooting Docker Compose applications on TrueNAS SCALE 25.04 through 15 MCP tools and 9 domain skills.

## MCP tools (15)

| Tool | Purpose | REQ |
|---|---|---|
| `test_connection` | Verify TrueNAS connectivity | F001 |
| `get_system_info` | Report NAS version, hostname, pool health | F002 |
| `list_apps` | List deployed apps, optional state filter | F003 |
| `get_app_details` | Full config + runtime state for one app | F004 |
| `start_app` | Start a stopped app, confirm RUNNING | F005 |
| `stop_app` | Stop a running app, confirm STOPPED | F006 |
| `restart_app` | Redeploy an app (app.redeploy) | F007 |
| `validate_compose` | Validate Compose YAML syntax + security | F008 |
| `deploy_app` | Create bind-mount dirs + deploy via app.create | F009 |
| `update_app` | Update existing app's Compose in place | F010 |
| `delete_app` | Delete app, optionally remove volumes | F011 |
| `purge_app` | Stop + delete with volumes in one call | F012 |
| `get_app_logs` | Retrieve recent log lines | F013 |
| `get_docker_networks` | Read-only Docker network inventory | F014 |
| `verify_deployment` | App state + optional HTTP + TCP checks | F015 |

## Skills (9)

- **truenas-onboarding** — First-time setup and environment verification
- **truenas-discovery** — Discover existing apps, pools, and networks
- **truenas-storage-conventions** — Bind-mount layout, pool selection, UID/GID
- **truenas-deployment-planning** — Plan a new deployment before running tools
- **truenas-deploy-and-verify** — Full deploy + verify workflow
- **truenas-app-control** — Start/stop/restart/delete lifecycle
- **truenas-files** — Upload files to TrueNAS via filesystem.*
- **truenas-troubleshoot** — Diagnose failing apps from logs and state
- **truenas-purge** — Clean up failed or experimental deployments

## Slash commands (4)

| Command | Purpose |
|---|---|
| `/truenas-list` | List all deployed apps with state |
| `/truenas-status <app>` | Full status for one app |
| `/truenas-control <app> <start\|stop\|restart>` | Lifecycle control |
| `/truenas-upload <local> <remote>` | Upload a file to TrueNAS |

## Prerequisites

Set these in your environment (host `~/.claude/settings.json` env block, or shell):

```
TRUENAS_HOST=your-nas.local
TRUENAS_API_KEY=your-api-key
TRUENAS_USERNAME=pvnk          # optional, defaults to pvnk
TRUENAS_SSL_VERIFY=true        # optional, defaults to true
```

## Source

Full source + tests: `nebula-otter` project under `/workspace/truenas-plugin-refactored/nebula-otter/`.

Transport: JSON-RPC 2.0 over WSS `/api/current`, auth via `auth.login_ex` with `API_KEY_PLAIN` (TrueNAS 25.04 — ADR-008).
