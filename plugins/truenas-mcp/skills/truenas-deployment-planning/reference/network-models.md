# Network models

> Reference for `truenas-deployment-planning`. Covers patterns 1, 2,
> 3, 9, 10 from `docs/research/deployment-patterns-input.md` (raw
> research input).
> Per ADR-002, the converter never auto-attaches services to a
> network — the compose author declares `networks:` explicitly.

## TL;DR — pick the model per service

| Symptom / requirement | Model |
|---|---|
| Default app, no special needs | Bridge (one network) + port-publish |
| App has a backend DB / cache that must not touch the LAN | Bridge with **front/back split**, back `internal: true` |
| App needs L2 / multicast / mDNS (Home Assistant, IoT discovery) | `network_mode: host` |
| App must own a routable LAN IP (Pi-hole, AdGuard on :53) | macvlan |
| Need to isolate container traffic to a specific physical NIC | bridge bound to a host-level Linux bridge on that NIC |

## Bridge — the default

Use this when the app is a normal containerised service that talks
to other containers via TCP/UDP and exposes a handful of ports to
the LAN. This is the right model for ~90% of deployments — anything
that does not need Layer-2 broadcasts, multicast discovery, or its
own routable IP. Do NOT use this when you need mDNS scanning of the
LAN, or when an app must bind a privileged port that the host
already owns.

Services on the same bridge resolve each other by service name via
Docker's embedded DNS — a `grafana` service on the same bridge as
`prometheus` reaches it at `http://prometheus:9090` without any
port-publish. Only publish what the host needs externally. If two
apps want the same host port, change the host-side mapping (e.g.
`3001:3000` instead of `3000:3000`) and verify with `list_apps`
that no other deployed app already owns it.

On TrueNAS 25.04 the 25.04 custom-app converter ships the bridge
declaration verbatim — there is no auto-attachment (ADR-002).

```yaml
services:
  grafana:
    image: grafana/grafana:11.0.0
    ports: ["3000:3000"]
    networks: [<apps-net>]
  prometheus:
    image: prom/prometheus:v2.54.0
    networks: [<apps-net>]

networks:
  <apps-net>:
    driver: bridge
```

## Front / back split (pattern 1)

Use this when the stack has any backend that has no business being
reachable from the LAN — databases, caches, queues, internal APIs.
The reverse proxy (or web tier) lives on a **front** network that
the LAN reaches; the database lives on a **back** network declared
`internal: true`. The app tier sits on both and bridges them. Do
NOT use a single flat network for any stack with a database — a
compromised proxy must not have a direct path to the data layer.

`internal: true` on a network means Docker creates no NAT/gateway
to the host's default route. Services on that network can still
talk to each other by service name, but the network itself has no
egress and is unreachable from outside the docker daemon. This is
the cheapest, most reliable form of network-layer isolation Docker
offers.

The names must be declared in the compose itself — the TrueNAS
converter does not invent them, per ADR-002.

```yaml
services:
  proxy:
    image: nginx:1.27-alpine
    ports: ["443:443"]
    networks: [<proxy-net>, <apps-net>]
  app:
    image: <app>:latest
    networks: [<apps-net>, <backend-net>]
  db:
    image: postgres:16-alpine
    networks: [<backend-net>]

networks:
  <proxy-net>:
    driver: bridge
  <apps-net>:
    driver: bridge
  <backend-net>:
    driver: bridge
    internal: true
```

## Host network (pattern 2)

Use this when the container must speak Layer-2 protocols — mDNS,
multicast, UPnP, SSDP, DHCP discovery. Home Assistant scanning the
LAN for Hue bridges or Sonos speakers is the canonical case. Do
NOT use host mode for any service that does not need broadcast or
multicast — it discards Docker's port-level isolation for no gain.

The reason bridge networks break these protocols: Docker's default
bridge does not forward multicast or broadcast packets between the
LAN and the container's isolated subnet. The container sees only
its own bridge IP space and never receives the discovery beacons.
With `network_mode: host`, the container shares the host's network
namespace and sees the LAN exactly as the host does.

The caveat is port collision: a host-mode container's listening
ports collide directly with the host. Only one app per host port,
and the host's own services (SSH on 22, the TrueNAS web UI on 80
or 443) are off-limits. The TrueNAS 25.04 converter passes
`network_mode: host` through unchanged.

```yaml
services:
  homeassistant:
    image: homeassistant/home-assistant:stable
    network_mode: host
    volumes:
      - /mnt/<pool>/<app>/config:/config
```

## Macvlan (pattern 9)

Use this when an app must own a routable LAN IP — typically a DNS
server on port 53 (Pi-hole, AdGuard) that would otherwise collide
with the host's resolver, or services where per-app IP makes
firewall and access-log rules cleaner. Do NOT use macvlan as a
casual default — every container on the macvlan sits directly on
the LAN, which is exactly the foot-gun ADR-002 was written to
prevent.

Properties: the container gets its own MAC address and a routable
IP from the configured subnet. From the LAN it appears as a
distinct device, indistinguishable from a physical host. There is
no port-publish step — every container port is reachable on that
LAN IP.

The sharp edge: by default the Linux kernel BLOCKS direct
host ↔ macvlan-container traffic. They sit on the same logical
subnet but cannot ping each other. Anything that needs to talk to
the container from the host (a health-check script, a backup job)
will fail until a separate host-shim interface is configured.
Surface this to the user before recommending macvlan.

```yaml
services:
  dns:
    image: adguard/adguardhome:latest
    networks:
      <apps-net>:
        ipv4_address: 192.168.1.20
networks:
  <apps-net>:
    driver: macvlan
    driver_opts:
      parent: <your-parent-iface>
    ipam:
      config:
        - subnet: 192.168.1.0/24
          gateway: 192.168.1.1
```

## Multi-NIC binding (pattern 10)

Use this when the NAS has 2+ physical NICs and the operator wants
container traffic on a specific NIC — separated from host
management traffic, or routed to a different LAN segment. Common
case: a download node that should not contend with the management
NIC for bandwidth. Do NOT use this on a single-NIC host; the
extra layer of indirection buys nothing.

This is a two-step setup. (1) The host OS creates a Linux bridge
bound to the target NIC — done via Netplan, `/etc/network/interfaces`,
or the TrueNAS network UI; that step is out of scope for this
reference. (2) The compose declares a bridge network that points
at the host-level bridge by name via the
`com.docker.network.bridge.name` driver option.

The result: every packet that leaves the container traverses the
designated NIC, and the rest of the host keeps using its primary
interface. The MCP server only ships the docker-side declaration;
the host bridge must already exist on the TrueNAS OS layer before
the app is deployed.

```yaml
services:
  download-node:
    image: <app>:latest
    networks: [<apps-net>]

networks:
  <apps-net>:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: <your-host-bridge>
```

## Compose conversion notes

- The TrueNAS 25.04 custom-app schema accepts the compose as
  `custom_compose_config_string`. Network declarations carry
  through verbatim.
- ADR-002 forbids the MCP server from silently attaching services
  to any discovered network. Discovery surfaces what exists;
  planning decides; the compose declares.
- Names that appear in this document (`<apps-net>`, `<backend-net>`,
  `<proxy-net>`) are placeholders. Resolve them against the NAS
  profile from `truenas-discovery`.
