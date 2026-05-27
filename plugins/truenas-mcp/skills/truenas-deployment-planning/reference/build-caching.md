# Build caching

> Reference for `truenas-deployment-planning`. Covers pattern 8 from
> `docs/research/deployment-patterns-input.md` (raw research input).
> Use when the deployment builds a custom image (rather than pulling
> a pre-built tag).

## Default — do not build

Pull pre-built images with immutable tags (`<image>:1.2.3`, never
`:latest`). Building on the NAS adds CPU load, occupies the docker
daemon's build cache space, and creates a CI burden for no gain in
most cases. Reach for a custom build only when one of the triggers
below applies — and even then, pin your own builds with an explicit
tag (`<your-registry>/<image>:1.0.0`) so the hardening rule about
pinned tags still applies.

If the only reason you are building is "I want to bake in a small
config file", a bind mount over `/mnt/<pool>/<app>/config` solves
the same problem without a custom image at all.

## When building is the right answer

| Trigger | Why build |
|---|---|
| Image contains a multi-GB asset (LLM weights, datasets, ML models) | Pulling the asset on every container start is unbearable — bake it in |
| The upstream image lacks something you must add (system tool, custom font, ICU data) | Forking the Dockerfile beats forking the runtime |
| Air-gapped or licensing-restricted base image | You must rebuild from a known-good base inside the controlled environment |
| Need to strip an upstream image of a known-vulnerable component | Removing files post-pull is fragile; rebuild from a slim base |

If none of the above applies, stop and pick a published tag.

## Anti-pattern — `COPY . .` early

The most common build-cache mistake is copying the entire source
tree at the *start* of the Dockerfile, before any expensive step.
Docker invalidates the cache for every layer below a changed file —
so any source edit forces a full rebuild of dependencies, asset
downloads, and everything else that follows.

The example from the raw research input — a Python service that
bakes in an LLM model — makes the cost concrete:

```dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN python download_llm.py  # re-runs on every source change
```

Each edit to a single Python file invalidates the `COPY . .` layer,
which invalidates `pip install` (minutes) and the model download
(potentially hours and many GB of bandwidth). The Dockerfile
*compiles* on every change.

The mistake is structural: heavy work runs *after* cheap, volatile
work. The fix is to reverse the order.

## Best practice — dependency layers first, asset cache, sources last

Order layers from least-volatile (changes once a month) to
most-volatile (changes every commit). Use BuildKit's
`--mount=type=cache` for downloads that are expensive but
reproducible from a checksum — package indexes, model weights,
dataset shards. The cache survives across builds even when the
layer that produced it is rebuilt.

```dockerfile
# syntax=docker/dockerfile:1.4
FROM python:3.11-slim
WORKDIR /app

# 1. Dependencies (change least often)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Heavy assets via BuildKit cache mount
RUN --mount=type=cache,target=/root/.cache/huggingface \
    python -c "from transformers import AutoModel; AutoModel.from_pretrained('<model-id>')"

# 3. Source code (changes most often)
COPY . .
CMD ["python", "main.py"]
```

**Layer-by-layer cache behaviour.**

- *Base image* (`FROM python:3.11-slim`): pulled once, reused
  forever until you bump the tag.
- *Requirements layer* (`COPY requirements.txt`, `pip install`):
  invalidated only when `requirements.txt` changes — i.e. when
  the dependency set actually shifts. `--no-cache-dir` prevents
  pip from writing its *internal* cache into the image (which
  would double the layer size).
- *Asset layer* (`--mount=type=cache`): the model download itself
  runs whenever the layer is rebuilt, but reads from the BuildKit
  cache mount first. As long as the cache mount survives (which
  it does across builds on the same host), the bytes never leave
  the daemon.
- *Source layer* (`COPY . .`): invalidated on every source edit,
  but it sits below everything expensive — invalidation is cheap.

**Header line.** The `# syntax=docker/dockerfile:1.4` (or newer)
header is required for `--mount=type=cache` syntax. Without it,
older Dockerfile parsers silently treat the `RUN --mount=...` as
plain `RUN` and the cache directive is ignored — the build still
works but the cache benefit vanishes.

## TrueNAS-25.04 specifics

- The TrueNAS docker daemon supports BuildKit; on some setups the
  build invocation must pass `DOCKER_BUILDKIT=1` (or `buildx`) so
  the cache-mount syntax is honoured. Verify by checking that the
  build output mentions BuildKit (`#1 [internal] load build
  definition`), not legacy builder output.
- The build cache lives on the TrueNAS host's docker layer store,
  *not* in the ZFS pool. It is ephemeral — daemon restarts, prune
  jobs, and disk pressure can clear it. Treat the cache as a
  speed-up, never a source of truth.
- Build artifacts that must persist (the final image, the
  resulting tag) belong in a registry the NAS can pull from. The
  app's runtime data still lives in bind-mounted dirs under
  `/mnt/<pool>/<app>/` per `storage-mounts.md`.
- Per ADR-003 the converter sends `app_name`, `custom_app`,
  `custom_compose_config_string` — the compose references the
  built image by tag. The build itself is out of band; the MCP
  server does not invoke `docker build`.

## Common pitfalls

- **Forgetting `--no-cache-dir` in `pip install`.** Pip writes its
  download cache to `~/.cache/pip` inside the image, doubling the
  layer size with content that the image never needs at runtime.
  `--no-cache-dir` skips it.
- **Missing the `# syntax=` header.** BuildKit cache-mount syntax
  silently degrades to a plain `RUN` — the build still completes,
  the model still downloads, but the cache directive does nothing.
  Always pin a Dockerfile syntax version when using `--mount`.
- **Using `:latest` for the base image.** Defeats reproducibility:
  `python:3.11` is fine (minor version is stable enough), but
  `python:latest` invites silent major-version drift on the next
  rebuild. The hardening rule (`hardening-rules.md`) applies to
  bases too.
- **Mixing the build cache with the runtime data path.** A bind
  mount under `/mnt/<pool>/<app>/data` is for runtime persistence;
  it is NOT a build cache. The build cache lives on the docker
  daemon's storage layer and is invisible to the running container.
- **Re-baking assets that should be bind-mounted.** If an "asset"
  changes weekly (a config file, a content library), it does not
  belong in the image — bind-mount it instead. Bake only data
  whose lifecycle matches the image (model weights for that
  release, ICU tables, etc.).
