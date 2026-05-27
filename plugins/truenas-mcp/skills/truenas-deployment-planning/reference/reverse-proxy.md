# Reverse proxy patterns

> Reference for `truenas-deployment-planning`. Covers pattern 4 from
> `docs/research/deployment-patterns-input.md` (raw research input).

## TL;DR — pick the provider per target

| Targets reachable | Provider | Why |
|---|---|---|
| Only container services | Docker labels | Self-registering, zero static config |
| Some targets are external (LAN host, physical NAS at IP) | File provider (YAML) | Labels can't describe non-Docker targets |
| Mixed | Both providers active simultaneously | Traefik supports multiple providers at once |

Traefik separates **static** configuration (how Traefik itself
starts — providers, entrypoints, TLS resolvers) from **dynamic**
configuration (how requests are routed). The decision below is
about the dynamic side: where the router and service definitions
live.

## Variant A — Docker labels

Use this when every routing target is a container running under
the same Docker daemon as Traefik. The Traefik container watches
the Docker socket and self-registers routes from labels attached
directly to each target service. Do NOT use labels when a route
target is anything other than a docker container — labels cannot
describe a backend that lives outside the daemon.

The non-negotiable security rule:
`--providers.docker.exposedbydefault=false`. With the default
`true`, every container that joins Traefik's network is silently
routable from the LAN — a fresh `postgres` container becomes a
public HTTP target the moment it starts. Forcing `false` makes
each app opt in with `traefik.enable=true`.

Socket mount must be read-only: `:ro`. Traefik only reads container
metadata; write access would let a compromised proxy create, modify,
or destroy containers on the host. The TrueNAS 25.04 converter
passes labels and socket mounts through unchanged, but it does not
inject Traefik's network into other services — per ADR-002 each
app declares the proxy network explicitly.

```yaml
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.websecure.address=:443"
    ports: ["443:443"]
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks: [<proxy-net>]

  <app>:
    image: <app>:latest
    networks: [<proxy-net>]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.<app>.rule=Host(`<your-domain>`)"
      - "traefik.http.routers.<app>.entrypoints=websecure"
      - "traefik.http.routers.<app>.tls=true"
      - "traefik.http.services.<app>.loadbalancer.server.port=80"

networks:
  <proxy-net>:
    driver: bridge
```

## Variant B — File provider

Use this when at least one routing target is **not** a container
under this Docker daemon — a TrueNAS service on the host, a
physical NAS at a fixed LAN IP, an external API, a hypervisor
management interface. The router and service definitions live in
a YAML file mounted into the Traefik container, and Traefik
watches that file for changes. Do NOT use the file provider for
purely-containerised stacks; labels are simpler and self-document
at the service they describe.

The static config (command-line or `traefik.yml`) points at the
dynamic file's path. The dynamic file defines routers (the rule
that matches incoming traffic) and services (the upstream targets).
A typical entry forwards `Host(<your-domain>)` to
`http://192.168.1.50:5000`, a placeholder for a LAN backend at a
fixed IP. Mount the file `:ro` — Traefik only needs to read it.

Both providers can be active at the same time: containers under
the daemon configure themselves via labels while external targets
live in the YAML. Treat the file as part of the deployment
artifacts and version it alongside the compose.

```yaml
# docker-compose.yml (Traefik start)
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--providers.file.filename=/etc/traefik/dynamic.yml"
      - "--entrypoints.websecure.address=:443"
    ports: ["443:443"]
    volumes:
      - ./dynamic.yml:/etc/traefik/dynamic.yml:ro
    networks: [<proxy-net>]

networks:
  <proxy-net>:
    driver: bridge
```

```yaml
# dynamic.yml
http:
  routers:
    external-nas:
      rule: "Host(`<your-domain>`)"
      entrypoints: ["websecure"]
      service: "nas-service"
      tls: {}
  services:
    nas-service:
      loadBalancer:
        servers:
          - url: "http://192.168.1.50:5000"
```

## TrueNAS-25.04 specifics

- The compose for Traefik runs as any other app under the 25.04
  custom-app schema: declare `networks:` explicitly, mount the
  docker socket `:ro` only.
- Apps that want to be routed share Traefik's network; the apps'
  labels are read by Traefik through the socket.
- Per ADR-002, the converter does not inject the proxy network
  into app services — the compose author adds it.
- TrueNAS 25.04 does not bind port 443 itself in a default
  install, but verify with `list_apps` before publishing — a
  previously deployed reverse proxy could already own it.

## Common pitfalls

- `--providers.docker.exposedbydefault=true` (default) routes
  every container — explicit security regression that turns a
  fresh `postgres` into a public HTTP target.
- Mounting the socket without `:ro` — Traefik does not need write
  access; refusing it follows least-privilege.
- Mixing label and file routing for the *same* service — both
  providers register the route, and behaviour depends on load
  order. Pick one provider per service.
- Missing `tls:` block on a router that listens on `websecure` —
  TLS termination fails silently in some configurations; the
  router accepts the request but never completes the handshake.
- Forgetting to attach the target service to the proxy network.
  Per ADR-002 this is never automatic; an app that lacks
  `networks: [<proxy-net>]` is unreachable from Traefik no matter
  what its labels claim.
