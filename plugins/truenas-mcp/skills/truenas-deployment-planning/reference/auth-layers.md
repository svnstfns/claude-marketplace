# Auth layer patterns

> Reference for `truenas-deployment-planning`. Covers pattern 5 from
> `docs/research/deployment-patterns-input.md` (raw research input).
> Use when an app has no authentication of its own and you need to
> gate it behind one.

## TL;DR — pick by user population

| User population | Variant |
|---|---|
| Self-hosted users, you control the directory | Authelia + Traefik `forwardAuth` |
| External users (GitHub / Google logins) | `oauth2-proxy` + Traefik `forwardAuth` |
| App already has auth | none — do not stack |

## Concept — Traefik `forwardAuth` middleware

Both variants below ride on the same mechanism: Traefik's
`forwardAuth` middleware. When a request matches a router that has
the middleware attached, Traefik does not forward the request
straight to the app — it first issues a sub-request to the auth
service. If the auth service answers 2xx the original request is
passed through to the app; any other response (typically a 302 to
a login page) is returned to the user verbatim. The auth service's
response headers can carry identity attributes back to the app via
`authResponseHeaders`.

Request flow:

```
User ──► Traefik ──► AuthService (verify)
                         │
              2xx ◄──────┘
                         │
User ◄── App ◄── Traefik (forward original request)
```

The contract is identical for Authelia and `oauth2-proxy` — they
differ only in HOW they answer "is this user authorised", not in
the Traefik wiring.

## Variant A — Authelia (self-hosted, your own user directory)

Use this when you control the user list, want MFA (TOTP, WebAuthn,
hardware keys) without a third-party dependency, and the
deployment is on-prem where external SSO either is not desired or
is not reachable. Do NOT use this when the user population is
external and unknown — running an open registration on Authelia
adds operational burden that an external IdP would have absorbed.

User directory options: a file-based YAML (`users_database.yml`),
LDAP, or a SQL database — Authelia supports all three. The
trade-off: you now run AND maintain Authelia. Config drift, TLS
renewals, and backups of the user database all become your problem.

Compose snippet (Traefik side — the middleware definition lives on
the Authelia service, so any other router can reference it):

```yaml
services:
  authelia:
    image: authelia/authelia:4
    volumes:
      - /mnt/<pool>/<app>/authelia:/config
    networks: [<proxy-net>]
    labels:
      - "traefik.enable=true"
      - "traefik.http.middlewares.authelia-auth.forwardauth.address=http://authelia:9091/api/verify?rd=https://<your-domain>/"
      - "traefik.http.middlewares.authelia-auth.forwardauth.trustForwardHeader=true"
```

Compose snippet (protected app — opts in via the `middlewares`
label):

```yaml
services:
  <app>:
    image: <app>:latest
    networks: [<proxy-net>]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.<app>.rule=Host(`<your-domain>`)"
      - "traefik.http.routers.<app>.middlewares=authelia-auth@docker"
```

## Variant B — `oauth2-proxy` (external identity provider)

Use this when users are external, you do not want to manage
passwords, and you are willing to delegate identity to GitHub,
Google, GitLab, or any other supported provider. Do NOT use this
when the user population is internal and you want offline
authentication — a provider outage becomes a login outage.

Provider config is driven entirely by environment variables:
`OAUTH2_PROXY_PROVIDER`, `OAUTH2_PROXY_CLIENT_ID`,
`OAUTH2_PROXY_CLIENT_SECRET`, `OAUTH2_PROXY_COOKIE_SECRET`, and
typically `OAUTH2_PROXY_EMAIL_DOMAINS` to scope which accounts may
log in. Secrets MUST come from env or a mounted secret file — never
literals in the compose YAML.

Compose snippet (`oauth2-proxy` side — middleware definition lives
on this service):

```yaml
services:
  oauth2-proxy:
    image: quay.io/oauth2-proxy/oauth2-proxy:v7
    environment:
      - OAUTH2_PROXY_PROVIDER=github
      - OAUTH2_PROXY_CLIENT_ID=${OAUTH2_PROXY_CLIENT_ID}
      - OAUTH2_PROXY_CLIENT_SECRET=${OAUTH2_PROXY_CLIENT_SECRET}
      - OAUTH2_PROXY_COOKIE_SECRET=${OAUTH2_PROXY_COOKIE_SECRET}
      - OAUTH2_PROXY_EMAIL_DOMAINS=<your-domain>
      - OAUTH2_PROXY_HTTP_ADDRESS=0.0.0.0:4180
    networks: [<proxy-net>]
    labels:
      - "traefik.enable=true"
      - "traefik.http.middlewares.github-auth.forwardauth.address=http://oauth2-proxy:4180"
      - "traefik.http.middlewares.github-auth.forwardauth.trustForwardHeader=true"
      - "traefik.http.middlewares.github-auth.forwardauth.authResponseHeaders=X-Auth-User,X-Auth-Email"
```

Compose snippet (protected app — same `middlewares` label, different
middleware name):

```yaml
services:
  <app>:
    image: <app>:latest
    networks: [<proxy-net>]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.<app>.rule=Host(`<your-domain>`)"
      - "traefik.http.routers.<app>.middlewares=github-auth@docker"
```

## TrueNAS-25.04 specifics

- Proxy, auth service, and protected app run as separate compose
  services in the same TrueNAS app, or as separate apps that
  share `<proxy-net>` declared in each compose.
- Secrets (OAuth client secret, cookie secret, Authelia JWT secret)
  belong in env vars sourced from the TrueNAS secret store or a
  mounted file — never inline in the compose YAML, never on the
  `command:` line (where they appear in process listings).
- Per ADR-002 the converter does not inject `<proxy-net>` into the
  app services — every service that needs to be reachable through
  Traefik must declare the network explicitly.

## Common pitfalls

- Missing `trustForwardHeader=true` on the middleware definition —
  Traefik strips the original headers, the auth service sees only
  the inter-container request, every auth attempt fails.
- OAuth provider redirect URL misconfigured at the provider — login
  succeeds at GitHub / Google, then the bounce-back lands on an
  unreachable URL. Verify the callback in the provider's app
  settings before deploying.
- `OAUTH2_PROXY_COOKIE_SECRET` left as a literal in the compose
  YAML or passed on the `command:` line — secrets leak into the
  process table and any log that captures docker inspect output.
  Always use env variables sourced from a secret store.
- Stacking app-internal auth and a `forwardAuth` middleware on the
  same route — the user logs in twice, sessions get out of sync,
  and the protected app cannot distinguish "anonymous request from
  Traefik" from "rejected user". Pick exactly one auth layer per
  route.
