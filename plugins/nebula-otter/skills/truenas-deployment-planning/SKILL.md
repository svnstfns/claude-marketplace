---
name: truenas-deployment-planning
description: Decide the deployment architecture for a TrueNAS app — which network model, which storage placement, which auth layer if any, which build strategy, and the hardening gate — before any compose is built. Consumes the NAS profile from truenas-discovery. Hands off to truenas-deploy-and-verify with a finished compose that expresses the decisions.
---

# Plan a TrueNAS deployment

This skill turns a NAS profile (from `truenas-discovery`) + the user's
intent into a concrete architecture plan and then into a compose that
expresses that plan. It does not deploy. It does not invent. Every
fact comes from the profile or the user.

The MCP server is mechanism. The architecture decisions live here.

## When to use this

Run after `truenas-discovery` has produced a confirmed NAS profile,
on any request like:

- "Deploy <project> on the NAS"
- "Install <app> on TrueNAS"
- "Ship this stack to the NAS"

If discovery has not run in this session, run it first. If it has,
you already have the profile in context — do not re-discover unless
the user asks.

## Inputs

- **NAS profile** from `truenas-discovery` (facts + confirmed
  assumptions: pools, networks, naming convention, path convention)
- **User intent**: which app / stack to deploy, any special requirements

## Phase A — Consume the profile

The profile gives you, *as facts*:
- Available pools and their health
- Existing docker networks (bridge / macvlan / etc.)
- Apps already deployed (for visual context)

*As confirmed assumptions*:
- Naming convention for app names
- Path convention for bind mounts (`/mnt/<pool>/<app>/...` form)
- Pool workload assignment (which pool is meant for which workload)
- Apps network candidate (if discovery proposed one)

You do not call any tool here. You consume the profile.

## Phase B — Core architecture decisions (always walked)

Five points. For each, apply the default; check the special case; if
the special case fires, open the linked reference file for the
compose snippet and rationale.

| # | Decision | Default | Special case | Reference |
|---|---|---|---|---|
| B.1 | Reverse proxy | Traefik + Docker labels | external LAN target → file provider | [reference/reverse-proxy.md](reference/reverse-proxy.md) |
| B.2 | NAS UI behind RP | not behind RP | only on explicit user request (warn loudly) | (inline below) |
| B.3 | NIC binding | default bridge | dedicated NIC for container traffic | [reference/network-models.md](reference/network-models.md) |
| B.4 | Per-app IP | bridge + port-publish | mDNS / multicast → host mode; DNS server on :53 → macvlan | [reference/network-models.md](reference/network-models.md) |
| B.5 | Storage mount | bind `/mnt/<pool>/<app>/` per profile path convention | shared cross-host → CIFS | [reference/storage-mounts.md](reference/storage-mounts.md) |

### B.2 — NAS UI behind RP — sharp edge

TrueNAS does not expect its admin UI to be reverse-proxied. The web
UI has no first-class setting for it; misconfiguration can lock the
operator out. Recommend keeping the admin UI on its direct address.
Only proceed behind the RP if the user explicitly asks AND
acknowledges the risk.

## Phase B+ — Conditional decisions

Four points. Walk a point only if its trigger applies. If none apply,
skip to Phase C.

| # | Trigger | Decision | Reference |
|---|---|---|---|
| B+.1 | The app has a backend DB / cache / queue inside its compose | Service-internal topology — split into front-net + back-net, back `internal: true` | [reference/network-models.md](reference/network-models.md) |
| B+.2 | The app has no built-in auth AND must not be public | Auth layer — Authelia (self-hosted) or oauth2-proxy (social) via Traefik `forwardAuth` | [reference/auth-layers.md](reference/auth-layers.md) |
| B+.3 | The app needs to see the docker socket | Socket exposition — `:ro`, Portainer Agent, or docker-socket-proxy | [reference/socket-exposition.md](reference/socket-exposition.md) |
| B+.4 | The compose builds a custom image | Build vs pull — pull pinned tag preferred; if build, BuildKit cache | [reference/build-caching.md](reference/build-caching.md) |

## Phase C — Hardening gate (always walked)

Before hand-off, run the compose through the veto checklist in
[reference/hardening-rules.md](reference/hardening-rules.md). Seven
rules; each is a hard veto. If any rule is violated, fix the compose
or get an explicit waive from the user (with reason) before
continuing.

## Phase D — Hand off

Build the `docker-compose.yml` so its `networks:`, `ports:`,
`volumes:`, and `labels:` express the decisions from Phases B / B+ /
C. Per ADR-002, the converter does not inject anything — the compose
must declare everything it needs.

Then call `truenas-deploy-and-verify` with `app_name` and the
compose YAML. That skill executes validate → deploy → verify →
diagnose.

## What this skill never does

- Deploy. That is `truenas-deploy-and-verify`.
- Invent a pool, network, or hostname. All three come from the
  profile.
- Adopt an inferred convention silently. Use the profile's
  confirmed values.
- Place a service on an externally-reachable network unless the
  architecture explicitly calls for it (ADR-002).
- Skip the Phase-C veto. The hardening checklist is mandatory; the
  user can waive individual rules with reason, never silently.
