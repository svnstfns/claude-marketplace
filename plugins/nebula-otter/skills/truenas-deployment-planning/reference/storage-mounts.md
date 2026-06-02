# Storage mounts

> Reference for `truenas-deployment-planning`. Covers pattern 7 from
> `docs/research/deployment-patterns-input.md` (raw research input),
> with TrueNAS / ZFS specifics.

## ZFS vocabulary (brief)

- **Pool**: top-level ZFS storage unit, addressed as `/mnt/<pool>/`
  on the host. The pool name (`<pool>` in this document) comes from
  `truenas-discovery` — it is a per-NAS convention, not a fixed
  string. Treat any literal pool name in upstream tutorials as an
  example, never as an assumption.
- **Vdev**: a group of physical devices (mirror, raidz, single)
  inside the pool. Invisible at the compose level; the operator
  sees only the pool.
- **Dataset**: a virtual filesystem under a pool, addressed as
  `/mnt/<pool>/<dataset>/`. Datasets are the unit of snapshot and
  replication policy on TrueNAS.
- **ZVOL**: a block-device child of the pool, used for iSCSI /
  block-storage targets. Not relevant for Docker bind mounts.
- **Snapshot**: read-only point-in-time copy of a dataset. Created
  in the TrueNAS UI or scheduler; the MCP server does NOT take
  snapshots and bind-mounting *into* a snapshot mount point is an
  anti-pattern (see pitfalls).

## Mount types

| Type | When |
|---|---|
| Bind to `/mnt/<pool>/<app>/...` | TrueNAS 25.04 default; matches the converter's expectations |
| Named docker volume | Avoid unless the app cannot do without it; harder to back up at ZFS level |
| CIFS / SMB driver | Cross-host shared media (Jellyfin, Paperless on shared docs) |
| NFS driver | Same as CIFS, when SMB is not desired |

## Bind mounts on TrueNAS (the default)

Use this when the app is a normal containerised service whose
persistent data should land on the ZFS pool — config, databases,
content libraries, anything the user wants snapshotted or replicated
through TrueNAS' own facilities. Do NOT use bind mounts when the
same files must also be visible to other docker hosts on the network
(use CIFS/NFS for that), or when the upstream image specifically
documents that it requires a named docker volume.

**Path layout.** The converter expects host paths under
`/mnt/<pool>/<app>/<subdir>`. The pool component comes from the
NAS profile produced by `truenas-discovery`; the app and subdir
components come from the compose author.

**Ownership.** TrueNAS apps run as UID 568 (GID 568) by default.
The converter `chown 568:568` on every new bind-mount host
directory before `app.create`, so the container can write from
first start. A manually pre-created directory under `/mnt/<pool>/`
must carry the same ownership — otherwise the container sees
`EACCES` / `EPERM`. This UID is fixed by the TrueNAS apps runtime;
do not override from the compose unless the upstream image
documents a different in-container user.

**Datasets vs. paths.** A dataset is a virtual filesystem under
the pool; granularity (one per app, one per data class, one giant
`apps` dataset) is a TrueNAS-UI decision made by the operator. The
compose just references the resulting host path — there is no
"dataset" concept inside the compose YAML. For per-app snapshot
policy, create a dedicated dataset (`/mnt/<pool>/<app>`) in the UI
before deploying; the compose then binds to that path and the
operator's snapshot schedule applies.

**ADR-003 wiring.** Per ADR-003 the converter only sends
`app_name`, `custom_app`, `custom_compose_config_string` to
`app.create`. Volume declarations live inside the compose YAML
that becomes the third field — there is no separate "volumes"
payload. The compose IS the deployment.

```yaml
services:
  <app>:
    image: <app>:1.2.3
    volumes:
      - /mnt/<pool>/<app>/config:/config
      - /mnt/<pool>/<app>/data:/data
    networks: [<apps-net>]
```

## CIFS / SMB driver_opts

Use this when several docker hosts must see the same files — a
Jellyfin instance whose libraries also live on a desktop share, a
Paperless deployment whose documents the user drops into an SMB
folder from their workstation, a media stack split across the NAS
and a secondary mini-PC. Do NOT use CIFS for state that lives on
this NAS only — a bind mount to `/mnt/<pool>/` is faster, snapshots
through TrueNAS, and avoids the SMB protocol surface entirely.

```yaml
services:
  jellyfin:
    image: jellyfin/jellyfin:10.9
    volumes:
      - shared_media:/data/media
    networks: [<apps-net>]

volumes:
  shared_media:
    driver: local
    driver_opts:
      type: cifs
      o: "username=<user>,password=${SMB_PASSWORD},uid=568,gid=568,vers=3.0"
      device: "//<host>/<share>"
```

Pin `vers=3.0` (or higher) on the `o:` option string. SMB1 and
SMB2 are deprecated, frequently disabled on modern shares, and
exposed to known protocol weaknesses. Credentials belong in an env
var (`${SMB_PASSWORD}`) or a docker secret, never literal in the
compose YAML — the YAML is checked into version control and the
converter surfaces it back through `app.update` payloads.

**TrueNAS context.** The CIFS mount is handled by the kernel's
`cifs` filesystem driver inside the docker daemon's mount namespace.
TrueNAS itself is not involved in the SMB chain — even when the
share happens to live on the same NAS, the path leaves the kernel
via SMB and re-enters it via SMB. For same-NAS data, prefer a bind
mount.

## NFS driver_opts

Same role as CIFS, when the share host serves NFS instead of SMB.
The shape is identical — replace `type: cifs` with `type: nfs`,
drop the username/password options, and point `device:` at the
`<host>:<path>` form (`192.168.1.50:/exports/media`). The same
caveat about leaving the kernel via the network applies.

## Named docker volumes

Use this when the upstream image insists on a named volume and the
data has no backup story you care about — a short-lived cache, a
scratch dir that the app regenerates on every restart, an
experimental deploy that you plan to delete next week. Otherwise:
do not.

**Why this is rarely right on TrueNAS.** Named volumes land under
`/var/lib/docker/volumes/`, *off* the ZFS pool — on the system
dataset. That means no ZFS snapshots, no dataset-level replication
tasks, no easy `zfs send` migration, no size accounting in the
pool's usage view. The data lives in a place TrueNAS' backup tools
don't see.

If you must use a named volume — because the image hard-codes the
path and offers no bind-mount alternative — add a comment in the
compose explaining why. Downstream operators wonder otherwise.

## Common pitfalls

- **Forgetting `chown 568:568` on a manually-created host dir.**
  The mount succeeds, the container starts, then writes fail. Fix:
  let the converter create the directory (it chowns automatically),
  or chown it yourself before `app.create`.
- **Bind-mounting a dataset that is itself a snapshot mount point.**
  Snapshot mounts are read-only and may disappear when the snapshot
  is destroyed. Bind to the live dataset path
  (`/mnt/<pool>/<dataset>/`), never to `.zfs/snapshot/...`.
- **CIFS against an SMB1/2-only host.** Pin `vers=3.0`; if the host
  cannot negotiate 3.0, the right fix is to upgrade the share host,
  not to downgrade the mount.
- **Docker volume name collisions across apps on TrueNAS.** The
  daemon is shared across all apps on the NAS — two apps that both
  declare a `data` named volume share the same backing store. Name
  volumes with an app-specific prefix (`<app>_data`) or, better,
  use bind mounts.
- **Mixing per-app dataset paths with cross-app shared paths.** If
  two apps need to see the same files, declare ONE shared bind
  mount under `/mnt/<pool>/<shared>/` rather than overlapping app
  subtrees that diverge in ownership.

## TrueNAS-25.04 specifics

- Converter expects bind sources rooted at `/mnt/<pool>/`; non-pool
  host paths are rejected at planning time.
- Bind directories are created with `chown 568:568` so the apps
  runtime can read and write from the first container start.
- Per ADR-003 the converter sends only `app_name`, `custom_app`,
  `custom_compose_config_string` — all volume declarations live
  inside the compose YAML.
- Snapshots happen at the ZFS dataset level via the TrueNAS UI or
  scheduler; the MCP server does not snapshot. Plan dataset
  granularity in the UI before deployment so per-app rollback is
  possible.
