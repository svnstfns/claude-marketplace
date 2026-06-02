---
name: truenas-app-control
description: Day-2 lifecycle control of deployed TrueNAS apps — start, stop, restart, update, and bulk operations across multiple apps. Use when the user says "start/stop/restart X", "update X", "restart everything that's stopped", or asks to operate running apps (not deploy or diagnose).
---

# Control TrueNAS apps

Operate already-deployed apps. This is not deployment (see
`truenas-deploy-and-verify`) and not diagnosis (see `truenas-troubleshoot`).

## Single-app actions
- Start: `start_app(app_name)` — polls until RUNNING.
- Stop: `stop_app(app_name)`.
- Restart: `restart_app(app_name)`.
- Update: `update_app(...)` — confirm the target image/config first.

Always confirm the app exists (`list_apps` / `get_app_details`) before
acting; report the returned `success`/`status`/`message`.

## Bulk operations
1. Resolve the target set with `list_apps(status_filter=…)` (e.g. all
   `STOPPED`).
2. Show the user the explicit list and the action; get confirmation.
3. Apply the action app-by-app, collecting per-app results.
4. Report a summary table: app → outcome. Never abort the whole batch on
   one failure — record it and continue.

## Safety
- Destructive verbs (delete/purge) are out of scope here — defer to
  `truenas-purge`.
- For `update`, surface what changes before applying.
