---
name: truenas-discovery
description: Capture the state of a TrueNAS NAS (pools, networks, deployed apps, inferred naming and path conventions) BEFORE any architecture decision is made. Use at the very start of any "deploy / install / set up X on the NAS" request, or whenever the agent needs a fresh picture of what exists on the NAS. Read-only; produces a structured NAS profile that downstream skills consume. Hands off to truenas-deployment-planning.
---

# Discover a TrueNAS NAS

This skill builds the **NAS profile** that every subsequent skill in
this plugin consumes. It is read-only: it reads the NAS state via the
MCP server's tool surface and presents what it found to you. It never
modifies anything on the NAS.

The MCP server is mechanism. Discovery is the eye: it tells the rest
of the pipeline what is *actually* there, so planning and deployment
do not have to guess.

## When to use this

Run this skill at the **start** of:

- "Deploy / install / ship <X> to the NAS"
- "What's running on the NAS?" (read-only inventory)
- Any session where the agent needs to know which pools, networks,
  or apps exist before it can answer

Do not run discovery if it has already produced a profile **earlier
in this conversation** AND the user has not asked for a refresh — the
profile is in-session state. If in doubt, run it again; it is read-only.

## Core principle — facts, assumptions, unknowns

Every claim Discovery makes falls into one of three buckets:

| Bucket | Source | How it's presented |
|---|---|---|
| **Fact** | A TrueNAS API call returned it | Stated plainly |
| **Assumption** | Derived from observed patterns (e.g. naming inference from existing apps) | Marked "assumption" with confidence; user confirms or corrects |
| **Unknown** | Not retrievable with current tools | Stated explicitly as "unknown" with reason |

An inference is never silently adopted. The output schema (below) keeps
the three buckets separate.

## Phase 1 — Connect

Call `test_connection`.

- If `connected == false`: stop. Show the error and recovery hint.
  Discovery cannot proceed without a session.
- Capture the TrueNAS version. Warn the user if it is below 25.04 — the
  `app.create` schema and the auth flow this plugin targets are 25.04+.

## Phase 2 — System and pools

Call `get_system_info`.

Capture as **facts**:
- TrueNAS version, hostname, uptime
- Storage pools: name, status, healthy

These are exact API answers. Do not invent pool names; use only the
ones the API returned.

## Phase 3 — Apps as a convention source

Call `list_apps`. For every app in the result, call
`get_app_details` in batches of up to 3 in parallel — wait for each
batch to complete before starting the next. This caps concurrent
API load without dropping coverage on installations with many apps.

From the collected app data, derive:

**Naming convention** (assumption, confidence-rated)
- Sample threshold = 3. If fewer than 3 apps exist, mark naming as
  "insufficient sample — no inference".
- Otherwise check pattern families:
  - Kebab-case lowercase: `^[a-z][a-z0-9-]+$` matches all → "kebab-case"
  - Trailing environment suffix: `-prod|-test|-staging` recurs → record suffix
  - Leading namespace prefix: `<prefix>-` recurs → record prefix
- Confidence:
  - `high` if all samples fit one pattern, ≥5 samples
  - `medium` if all samples fit, 3–4 samples
  - `low` if mixed or only barely consistent

**Path convention** (assumption, confidence-rated)
- Collect host paths from each app's `volumes` (bind mounts under
  `/mnt/`).
- Identify the modal form: `/mnt/<pool>/<app>/...` vs
  `/mnt/<pool>/apps/<app>/...` vs `/mnt/<pool>/<other-segment>/<app>/`.
- Mix → "no consistent convention".

**Pool workload assignment** (assumption)
- Count apps per pool. Surface the distribution.
- Mark as assumption: pool hardware type (NVMe / HDD / SSD) cannot
  be derived from the current tool surface. Pool *names* often hint
  at it (e.g. `<fast-pool>`, `<bulk-pool>`) — record the hint, ask
  the user to confirm.

## Phase 4 — Network inventory

Call `get_docker_networks`.

Capture as **facts**:
- Each network's name, driver, subnet, scope

Derive (assumption):

**Reverse-proxy / app network candidate**
- Heuristic A: name contains `proxy|traefik|caddy`
- Heuristic B: driver is `macvlan` AND ≥2 apps share it (requires
  the app detail data collected in Phase 3 — run Phase 3 first)
- Any match → propose as the "apps network candidate"; never adopt
  silently.

## Phase 5 — Build and present the NAS profile

Present the profile to the user in this exact shape:

```
NAS profile — <hostname> (TrueNAS Scale <version>)
═══════════════════════════════════════════════════

Facts (from API):
  TrueNAS version:      <version>
  Hostname:             <hostname>
  Uptime:               <uptime>
  Storage pools:
    <name>   <status>   <healthy>
    ...
  Docker networks:
    <name>   <driver>   <subnet>
    ...
  Apps deployed: <N>
    <name> (<status>) → pool <inferred-pool>
    ...

Assumptions (please confirm):
  Naming convention:    <pattern>             confidence: <low|medium|high>
                        sample size: <N>
  Path convention:      /mnt/<pool>/<app>/    confidence: <…>
  Pool workloads:
    <pool>: <N apps> — likely <inferred role>
    ...
  App network candidate: <name or "none detected">

Unknown (please clarify when relevant):
  - Vdev topology per pool (no MCP tool yet)
  - Pool hardware type (NVMe / HDD / SSD)
  - External-facing network identity (which network is LAN-routable)
```

Wait for the user to confirm or correct the assumptions before
handing off.

## Phase 6 — Hand off to planning

Once the user confirms (or corrects), say so explicitly and pass the
confirmed profile forward. From here:

- `truenas-deployment-planning` takes over for architecture decisions.
- For pure inventory questions ("what's running?"), this skill alone
  is sufficient; do not call planning unless the user wants to
  deploy / install / change something.

## What this skill cannot see today

The MCP server does not expose tools for:
- Vdev topology per pool (RAIDZ level, disk count, mirror layout)
- Dataset / ZVOL inventory under a pool
- Pool hardware type (NVMe vs spinning) directly

Mark these as "unknown" in the profile and ask the user when the
answer matters. Adding these tools is a separate future spec.

## What this skill never does

- Modify anything on the NAS (it is strictly read-only)
- Present an inference as a fact
- Pull host / pool / network name from any default value
- Claim a naming convention with fewer than 3 samples
- Cache the profile across sessions (each session starts fresh)
