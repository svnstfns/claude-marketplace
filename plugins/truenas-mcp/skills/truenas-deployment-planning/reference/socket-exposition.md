# Docker socket exposition

> Reference for `truenas-deployment-planning`. Covers pattern 6 from
> `docs/research/deployment-patterns-input.md` (raw research input).

## Rule of thumb

The Docker socket grants root-equivalent access to the host. Default:
**do not mount it**. If an app genuinely needs Docker visibility,
pick the narrowest pattern that satisfies it.

| Use case | Pattern |
|---|---|
| Traefik reading container labels | mount `:ro`, no write |
| Portainer / CI agent | Portainer Agent over TLS, never raw socket on the network |
| Production with multiple consumers | docker-socket-proxy with ACLs (read-only methods) |
| Remote management across hosts | never expose `:2375` / `:2376` — use the agent pattern |

## Pattern A — Read-only mount

Use this when a label-reader service like Traefik needs to enumerate
containers and read their labels, and nothing more. The `:ro` suffix
on the volume is the *entire* security boundary: without it the
container can call any Docker API method — `docker exec` into a
sibling, `docker run` a fresh container with `-v /:/host`, modify
the daemon's state. With `:ro` those write-side calls fail at the
kernel level before the daemon ever sees them.

Do NOT use this for any service that genuinely needs to act on
containers (restart, exec, network changes). A read-only mount
silently breaks those workflows; pick pattern B or C instead.

```yaml
services:
  traefik:
    image: traefik:v3.0
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks: [<proxy-net>]
```

The single character `:ro` is load-bearing. Without it Traefik can
take over the host through ONE compromised container.

## Pattern B — Portainer Agent (cross-host management)

Use this when a central Portainer server (or any management UI)
needs to manage a remote Docker node. The agent runs locally on the
remote node with full socket access; the central server talks to
the agent over a hardened TLS channel. The raw socket never crosses
a network boundary.

Why never raw socket on the network: exposing `tcp://:2375`
(unencrypted) or `tcp://:2376` (TLS server cert, no client auth by
default) makes ONE unauthenticated HTTP request enough to run
`docker run -v /:/host` and take full filesystem control. TLS on
the daemon protects the channel but does not authenticate the
caller — the cert chain is one-sided and trivially bypassed by
anyone on the wire.

```yaml
services:
  portainer_agent:
    image: portainer/agent:2
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /var/lib/docker/volumes:/var/lib/docker/volumes
    ports:
      - "9001:9001"
    networks: [<apps-net>]
    restart: unless-stopped
```

The agent mounts the socket RW (it must `exec` and `restart`
containers). The TLS-protected agent port replaces the raw socket
as the network-facing surface. Restrict the published port to a
known management subnet at the firewall layer.

## Pattern C — docker-socket-proxy (production hardening)

Use this when the host runs multiple consumers with *different*
access needs — e.g. Traefik (label reads only) plus a monitoring
agent (container metrics) plus a backup orchestrator (volume
listings). Each consumer would otherwise need its own socket
mount, each with the broadest access. A socket-proxy in front of
the real socket ACL-filters every HTTP call, so each consumer can
be granted only the verbs and endpoints it actually needs.

How it works: the socket-proxy service mounts the real socket RW
(it is the only thing that should). Consumers mount the proxy's
HTTP endpoint via `<proxy-socket-net>` instead of the real
`/var/run/docker.sock`. The proxy's env vars allow specific API
groups (`CONTAINERS=1`, `IMAGES=1`) and HTTP methods
(`POST=0`, `DELETE=0` keep it read-only).

```yaml
services:
  socket-proxy:
    image: tecnativa/docker-socket-proxy:latest
    environment:
      - CONTAINERS=1
      - IMAGES=1
      - POST=0
      - DELETE=0
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    networks: [<proxy-socket-net>]

  traefik:
    image: traefik:v3.0
    command:
      - "--providers.docker=true"
      - "--providers.docker.endpoint=tcp://socket-proxy:2375"
    networks: [<proxy-net>, <proxy-socket-net>]
```

Result: even if Traefik (or any other consumer) is compromised, the
proxy refuses the dangerous calls — `docker run`, `docker exec`,
`docker rm` all return 403. The blast radius is bounded by the ACL.

## Anti-pattern — raw socket over the network

NEVER bind `tcp://0.0.0.0:2375` or `tcp://0.0.0.0:2376` on any
docker daemon. The Docker daemon ships with no authentication on
its HTTP listener; exposing it to a network — even a "trusted" LAN
— means one HTTP request away from `docker run -v /:/host` and full
filesystem control as root.

TLS (`:2376`) is not a fix. The daemon's TLS server presents a
cert; nothing forces the client to present one. Even mutual TLS,
when correctly configured, is a brittle replacement for the agent
pattern, which exists *because* the raw socket on the wire is
unsafe.

This is the single hardest "do not" rule in the entire skill set.
If you find yourself reaching for raw `:2375`/`:2376`, stop and
deploy the Portainer Agent or a socket-proxy instead.

## TrueNAS-25.04 specifics

- TrueNAS apps run on the cluster docker daemon. The socket on the
  TrueNAS host is *that* cluster's socket — it sees every app
  running on the NAS, not just the sibling services in the same
  compose.
- An app that mounts the socket therefore has a blast radius of
  the entire NAS: control over the TrueNAS web UI's own helper
  containers, the user's other apps, every published port. Treat
  this as a property of the NAS, not of the app.
- ADR-002 does not directly speak to socket mounts, but the same
  spirit applies: the compose author declares the mount; the
  converter never adds one. A socket mount is an explicit,
  reviewed decision at the compose level.

## Common pitfalls

- Forgetting `:ro` on a Traefik socket mount — Traefik does not
  need write access. Refusing it follows least-privilege; granting
  it because "everyone does" gives the proxy a path to take over
  the host.
- Mounting the socket on a service that just "might need it later"
  — least-privilege says no until it actually does. The cost of
  adding the mount later when needed is far smaller than the cost
  of a compromise through an unnecessary mount.
- Treating TLS socket exposure (`:2376`) as a secure alternative —
  TLS encrypts the channel but does not authenticate clients by
  default. The cert validation is one-sided. Use the agent pattern.
- Mounting the socket and then publishing the consumer's port to
  the LAN — the socket becomes reachable through that consumer's
  HTTP surface. Bind the consumer to a private network, never to
  `0.0.0.0`.
