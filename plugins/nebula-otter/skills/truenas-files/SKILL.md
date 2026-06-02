---
name: truenas-files
description: Move files to/from TrueNAS dataset paths and manage directories — upload, download, list, delete, mkdir — applying the storage-conventions layout. Use when staging compose/config files, fetching logs/backups, or organizing an app's directories on the NAS.
---

# TrueNAS file management

Transfer and organize files on the NAS. Always apply
`truenas-storage-conventions` when choosing paths.

## Operations
- List: `list_dir(path)` — inspect a directory before acting.
- Make dir: `make_dir(path)` — create per-app subtrees (`data/config/logs`).
- Upload: `put_file(local_path, remote_path)` — stage compose/config.
- Download: `get_file(remote_path, local_path)` — fetch logs/backups.
- Delete: `delete_path(path, confirm=True)` — required `confirm` guard.

## Procedure for staging an app's files
1. Consult `truenas-storage-conventions`; compute the per-app root and
   subtrees.
2. `make_dir` each needed subtree.
3. `put_file` each file into its correct subtree (config files under
   `config/`, never under `data/`).
4. `list_dir` to confirm the result; report the tree.

## Safety
- Refuse ambiguous or convention-violating remote paths — ask the user.
- `delete_path` never runs without `confirm=True`; for app removal prefer
  `truenas-purge`.
