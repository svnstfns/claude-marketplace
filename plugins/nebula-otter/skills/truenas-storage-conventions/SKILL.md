---
name: truenas-storage-conventions
description: The naming and directory-layout rules for app storage on TrueNAS — per-app roots, separation of app-data from config and logs, and stable kebab-case names. Use when deciding where an app's files/volumes go, when staging files, or when another skill (deploy, files) needs the layout rules.
---

# TrueNAS app storage conventions

Apply these rules whenever placing an app's data, config, logs, or
compose/volume mounts on the NAS.

## Per-app root
- Each app gets one root: `/<pool>/apps/<app-name>/`
- `<app-name>` is **lowercase-kebab-case**, no spaces, stable across
  redeploys (it doubles as the app identifier).

## Separate subtrees (never co-mingle)
- `…/<app>/data/`   — application data (databases, user content)
- `…/<app>/config/` — configuration files
- `…/<app>/logs/`   — log output
- Never put logs under data; never put two apps under one root.

## Volume mapping
- Bind mounts in compose point at the matching subtree, e.g.
  `/<pool>/apps/paperless/data:/usr/src/paperless/data`.
- Create the subtrees (`make_dir`) before deploy.

## Why
Clean separation makes backups, snapshots, and retention policies
targetable per concern (snapshot `data/` aggressively, prune `logs/`),
and keeps app removal a single-root delete.
