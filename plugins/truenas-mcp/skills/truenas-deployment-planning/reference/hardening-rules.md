# Hardening rules (veto checklist)

> Reference for `truenas-deployment-planning`. Covers pattern 11 from
> `docs/research/deployment-patterns-input.md` (raw research input).
> This is the Phase-C gate. Each rule below is a veto: the compose
> must satisfy it, or planning halts and asks the user to fix it
> before hand-off to `truenas-deploy-and-verify`.

## The rules

| # | Rule | Why |
|---|---|---|
| 1 | Image tag is pinned (`<image>:<version>`, never `:latest`) | Reproducibility; `:latest` silently upgrades |
| 2 | Base image is `slim` / `alpine` / `distroless` when available | Smaller attack surface |
| 3 | Container runs non-root (`user:` directive set) | A vuln in the app does not yield host root |
| 4 | Externally-facing port-publish uses `127.0.0.1:<port>:<container-port>` when only the host needs access | Default `<port>:<container-port>` exposes to all interfaces |
| 5 | No secrets in the image or compose YAML | Secrets in env / secret store only |
| 6 | `restart: unless-stopped` on long-running services | Survives reboots without auto-restarting after explicit stop |
| 7 | `.dockerignore` excludes `.git`, `node_modules`, `__pycache__`, etc. when building | Smaller build context, no leakage |

## Enforcement

Planning walks the compose during Phase C and runs one explicit
check per rule:

- *Rule 1.* Parse each `services.*.image` string; reject `:latest`,
  reject any tag-less image (`postgres` with no colon defaults to
  `:latest`).
- *Rule 2.* Look at the base image suffix; warn (not veto) when an
  obvious slim variant exists upstream and the compose uses the
  fat one.
- *Rule 3.* For each service, verify `user:` is set OR the upstream
  image's documented default user is non-root. The default Docker
  behaviour is root — the rule fails if neither condition holds.
- *Rule 4.* Walk `services.*.ports`. Any string of the form
  `<port>:<container-port>` (no IP prefix) on a service that the
  user described as "host-local only" is a veto.
- *Rule 5.* Scan `services.*.environment` values for strings that
  match secret patterns (`*_PASSWORD=`, `*_TOKEN=`, `*_SECRET=`,
  `*_KEY=`) followed by a literal that is not an env interpolation
  (`${...}`). Same for the `command:` line.
- *Rule 6.* Check that every long-running service has a `restart:`
  policy. `unless-stopped` is preferred; `always` is acceptable;
  no policy at all on a daemon-style service is a veto.
- *Rule 7.* If the compose includes a `build:` directive, verify a
  `.dockerignore` exists in the build context root. (For pulled
  images this rule does not apply.)

On violation, planning halts and asks the user. The user MAY
explicitly waive a rule with a reason — the exact wording:

> "waive rule N: <reason>"

Anything less specific (a hand-wave, a "just deploy it") is not a
waiver. Each rule is waived per-deployment, not per-session.

## Anti-patterns explicitly forbidden

- **`image: foo:latest`.** Defeats reproducibility — the same
  compose deployed twice can yield different runtime behaviour.
  Pin the version; bump it deliberately.
- **`user: root` (or omitted, defaulting to root).** A
  remote-code-execution vuln in the app yields root in the
  container, and from there a path to the host (especially when
  the socket is mounted, see `socket-exposition.md`). The fix is
  trivial: `user: "568:568"` for TrueNAS apps, or the UID the
  upstream image documents.
- **`ports: - "8080:80"` on a service that only the host needs to
  reach.** Docker binds to `0.0.0.0` by default — the port is on
  every interface, regardless of any host firewall. Use
  `127.0.0.1:8080:80` to bind to loopback, or omit the
  port-publish entirely if a reverse proxy is in the picture.
- **`MYSQL_ROOT_PASSWORD: <literal>` in compose.** The literal
  appears in `docker inspect` output, in image history if it ever
  got committed, in every log scrape that captures container env.
  Use `${MYSQL_ROOT_PASSWORD}` and source the value from the
  TrueNAS secret store or a `.env` file outside version control.
- **Docker socket mounted RW without a justified pattern from
  `socket-exposition.md`.** Any service that mounts
  `/var/run/docker.sock` writable controls the host. Read-only
  (`:ro`) is the floor; the agent or socket-proxy pattern is the
  proper answer for write-side needs.

## TrueNAS-25.04 specifics

- **Loopback bind.** `127.0.0.1:<port>:<container-port>` keeps the
  service on the TrueNAS host loopback. Other apps on the same
  NAS can still reach it via the docker network (when they share
  a network declared in the compose, per ADR-002). The LAN
  cannot.
- **Host firewall does not gate docker.** TrueNAS' built-in
  firewall (and any host-level UFW / iptables rules the operator
  configured) does NOT mediate docker port-publishes. Docker's
  userland-proxy and direct iptables MASQUERADE rules bypass the
  host firewall — binding to `0.0.0.0` exposes to the LAN even
  when the operator believes their firewall is blocking the port.
  The rule-4 veto exists for this reason.
- **Secrets.** Prefer the TrueNAS secret store, env interpolation
  from a `.env` file kept off version control, or docker secrets
  over compose-embedded values. Never put a secret on a
  `command:` line — it appears in process listings on the host.
- **Non-root UID.** TrueNAS apps run as UID 568 by default; this
  satisfies rule 3 for any service that respects the `user:`
  directive. Some upstream images insist on running as root
  internally (init scripts that chown files, then drop privs) —
  for those, set `user:` only if upstream documents it as safe.
- **ADR-003 schema.** All veto checks operate on the compose YAML
  before it becomes the `custom_compose_config_string`. The
  converter's three-field payload carries the compose verbatim,
  so the rules must hold at compose time — no chance for a
  later layer to retroactively harden the deployment.

## Waive protocol

When the user accepts a justified deviation, planning records the
waiver in the architecture plan it hands off to
`truenas-deploy-and-verify`. The waiver text — the rule number,
the rule name, and the user's reason — appears in the PR or
deployment record so future audits can see what was accepted and
why.

Three constraints:

1. Never waive silently. If the user does not explicitly say
   "waive rule N: <reason>", the violation stays unresolved and
   planning does not proceed.
2. Never re-prompt for the same waiver within one deployment. The
   waiver applies to this compose, in this hand-off; the next
   deployment starts with a clean slate.
3. A waiver does not propagate across rules. Waiving rule 1 does
   not also waive rule 5 — even when the same root cause underlies
   both. Each rule is its own decision.
