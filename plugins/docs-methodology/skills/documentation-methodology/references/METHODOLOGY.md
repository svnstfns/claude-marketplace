# Documentation Methodology

> A lightweight, arc42-inspired, ID-anchored specification method for software projects driven by Claude Code.

**Status:** Authoritative reference
**Audience:** Humans + Claude Code (and any LLM-based coding agent)
**License of this doc:** Internal — copy freely into your own projects.

---

## 1. Philosophy

The method exists to enforce four properties on every project:

1. **Every implementation detail is traceable** back to a requirement, a decision, and a test.
2. **Every architectural choice has a recorded reason** (no folklore, no tribal knowledge).
3. **Every artifact is plain Markdown + YAML** — diffable, grep-able, LLM-readable.
4. **Lightweight by default** — only the artifacts that earn their keep are written.

This is **not** a heavyweight framework like TOGAF, TOSCA, or full SysML. It is a pragmatic skeleton built from:

- **arc42** (architecture views + ADRs, sections 3, 5, 7, 9 in particular)
- **Michael Nygard ADRs** (Architecture Decision Records)
- **IEEE/SWEBOK-style requirements** (functional vs. non-functional, atomic, testable)
- **Traceability matrix** (Requirement → Architecture → API → UI → Test → Implementation)
- **TDD** (test cases exist before implementation)
- **Conventional Commits** (parseable git history)

---

## 2. The ID System

Every artifact gets a stable ID. IDs are the only contract between layers. **Never rename an ID** — set status to `dropped` instead and link the replacement.

| Prefix | Scope | Example | File |
|---|---|---|---|
| `REQ-F###` | Functional requirement (3-digit, zero-padded) | `REQ-F010` | `docs/requirements/REQ-functional.md` |
| `REQ-NF###` | Non-functional requirement (3-digit, zero-padded) | `REQ-NF003` | `docs/requirements/REQ-nonfunctional.md` |
| `ADR-###` | Architecture Decision Record | `ADR-002` | `docs/architecture/ADR-002-<slug>.md` |
| `ARCH-<slug>` | Architecture view document | `ARCH-data-model` | `docs/architecture/ARCH-<slug>.md` |
| `API-<slug>` | API specification | `API-core-endpoints` | `docs/api/API-<slug>.md` |
| `UI-<slug>` | UI/UX specification | `UI-design-system` | `docs/ui/UI-<slug>.md` |
| `TC-###` | Test case | `TC-001` | `docs/requirements/REQ-testcases.md` |

**Rules:**
- IDs are immutable. A "renumbering" pass is forbidden.
- Numbers are assigned in creation order, never reordered.
- IDs are referenced by exact string (no fuzzy matching) so grep + LLMs find them deterministically.

---

## 3. Repository Layout

```
<project-root>/
├─ CLAUDE.md                        # Entry point for Claude Code (project rules)
├─ README.md                        # Human entry point
├─ docs/
│  ├─ requirements/
│  │  ├─ REQ-functional.md         # All REQ-F### entries
│  │  ├─ REQ-nonfunctional.md      # All REQ-NF## entries
│  │  └─ REQ-testcases.md          # All TC-### entries
│  ├─ architecture/
│  │  ├─ ADR-001-<slug>.md         # one ADR per file
│  │  ├─ ADR-002-<slug>.md
│  │  ├─ ARCH-system-overview.md   # arc42 §3 Context
│  │  ├─ ARCH-data-model.md        # arc42 §5 Building Blocks (data view)
│  │  ├─ ARCH-dataflow.md          # arc42 §6 Runtime
│  │  └─ ARCH-deployment.md        # arc42 §7 Deployment
│  ├─ api/
│  │  └─ API-<slug>.md
│  ├─ ui/
│  │  └─ UI-<slug>.md
│  ├─ research/                    # third-party tech notes (read-only context)
│  └─ traceability.yaml            # the spine
├─ src/                            # implementation
└─ tests/                          # unit + integration
```

**Hard rules:**
- `docs/` is the single source of truth. No spec lives in code comments.
- One ADR per file. ADRs are never edited after acceptance — they are superseded by a new ADR.
- ARCH documents are living documents and may be edited (but changes that flip a decision require a new ADR).

---

## 4. Artifact Specifications

### 4.1 Functional Requirement (`REQ-F###`)

Single atomic statement. Testable. Written in active voice.

```markdown
### REQ-F010 — Create crawl source

**Description:** The user can register a new crawl source by submitting a URL.
**Acceptance:**
- POST /api/sources with `{type: "web", url}` returns 201 + source_id
- Source appears in GET /api/sources within 1s
- Duplicate URLs return 409 Conflict
**Status:** active
**Tests:** TC-001, TC-002
```

### 4.2 Non-Functional Requirement (`REQ-NF##`)

Measurable. No vague adjectives ("fast", "secure") without a number or scenario.

```markdown
### REQ-NF003 — Search latency

**Quality attribute:** Performance
**Scenario:** A semantic search query over ≤100k chunks returns top-10 results in <500ms at p95 on the reference hardware (8 vCPU / 16GB RAM).
**Status:** active
**Tests:** TC-042
```

### 4.3 Architecture Decision Record (`ADR-###`)

Michael Nygard format. **One decision per file.** Immutable after status `accepted`.

```markdown
# ADR-002 — No MCP Protocol

**Status:** accepted
**Date:** 2026-03-19
**Supersedes:** —
**Superseded by:** —

## Context
Initial plan included an MCP server for LLM consumers. Investigation showed the
audience (LLMs + humans) is best served by a single REST API.

## Decision
Expose all functionality via REST (POST/GET/PUT). Do not implement MCP.

## Consequences
+ One transport to test, document, secure.
+ Standard HTTP tooling for both humans and LLMs.
− MCP-native clients need a thin adapter.

## Affects
- REQ-F050 (dropped)
- API-core-endpoints
```

**Status lifecycle:** `proposed` → `accepted` → (`deprecated` | `superseded`). Never delete.

### 4.4 Architecture View (`ARCH-<slug>`)

A living document covering one arc42 view. Recommended minimal set:

- `ARCH-system-overview.md` — context diagram (Mermaid), external systems, boundaries
- `ARCH-data-model.md` — entities, fields, relationships
- `ARCH-dataflow.md` — runtime sequences for the main scenarios
- `ARCH-deployment.md` — containers, ports, volumes, network topology

Add more views (`ARCH-security.md`, `ARCH-observability.md`, …) only when content exists to put in them.

### 4.5 API Specification (`API-<slug>`)

Endpoint by endpoint: path, method, request schema, response schema, error codes, examples. Prefer OpenAPI excerpts in fenced YAML blocks for machine readability.

### 4.6 UI Specification (`UI-<slug>`)

Screens, components, states, accessibility notes. Embed Mermaid for flows. Link to design system tokens.

### 4.7 Test Case (`TC-###`)

```markdown
### TC-001 — Create crawl source happy path

**Verifies:** REQ-F010
**Type:** integration
**Given:** Clean DB, API running
**When:** POST /api/sources {type: "web", url: "https://example.com"}
**Then:** 201 returned, body contains source_id, GET /api/sources/<id> returns the record
**Impl:** tests/integration/test_sources.py::test_create_source
```

---

## 5. Traceability — `docs/traceability.yaml`

The matrix is the spine. Every REQ has one entry. Each entry links downward to architecture, API, UI, tests, and code paths.

```yaml
- req: REQ-F001
  title: Create crawl source
  status: active                    # active | dropped | deferred
  arch: [ARCH-data-model]
  api: [API-core-endpoints#POST-sources]
  ui: [UI-tabs-sources#source-form]
  tests: [TC-001]
  impl: [src/api/routes/sources.py]

- req: REQ-F050
  title: MCP Server
  status: dropped
  note: "Replaced by REST API (ADR-002)"
  adr: [ADR-002]
```

**Rules:**
- A `req:` entry without `tests:` is incomplete (status must be `deferred` or `dropped`).
- A `status: dropped` entry must have `note:` and an `adr:` link to the supersession.
- `impl:` paths are repo-relative and must exist at HEAD.

**CI check (recommended):** lint that every REQ-F/REQ-NF in `docs/requirements/` has a `traceability.yaml` entry, and every linked path exists.

---

## 6. Workflow

### 6.1 Adding a new feature

1. Open `docs/requirements/REQ-functional.md`, add the next `REQ-F###` (highest existing + 1, zero-padded).
2. Add the test case to `docs/requirements/REQ-testcases.md` as the next `TC-###`.
3. If the feature requires a new architectural choice → write an ADR.
4. Update affected `ARCH-*.md` views.
5. Update `API-*` / `UI-*` if interfaces change.
6. Add the entry to `traceability.yaml`.
7. Write the failing test in code → make it pass → commit.

### 6.2 Changing a decision

1. Write a new ADR with `Status: accepted`.
2. Edit the old ADR header: `Status: superseded by ADR-NNN`.
3. Update `ARCH-*` views to reflect the new state.
4. Add a `note:` to affected `traceability.yaml` entries.

### 6.3 Dropping a requirement

1. Edit the REQ entry in `REQ-functional.md`: `**Status:** dropped`.
2. Update `traceability.yaml`: `status: dropped` + `note:` explaining why + `adr:` link.
3. Remove implementation if present (separate commit, referencing the REQ).

---

## 7. Conventions

### 7.1 Commits

Conventional Commits — `<type>(<scope>): <subject>`

```
feat(sources): add crawl source creation (REQ-F001)
fix(search): handle empty embedding matrix (TC-042)
docs(adr): add ADR-006 chunking algorithm
chore(ci): add traceability linter
```

Reference IDs in commit bodies whenever the change touches a tracked artifact.

### 7.2 Branches

`<type>/<issue-or-id>-<short-description>`

```
feat/REQ-F001-create-source
fix/TC-042-empty-matrix
chore/ADR-006-chunking
```

### 7.3 Code

- **TDD:** write the failing test (referencing a `TC-###`) before the implementation.
- **Type hints / strict types** on all public functions/exports.
- **Schemas at the boundary** (Pydantic in Python, Zod in TS) — never trust untyped JSON.
- **Async I/O** by default unless there's a reason not to.
- **Docstrings reference IDs** when behavior is mandated by a spec:

```python
def create_source(payload: SourceCreate) -> Source:
    """Create a crawl source (REQ-F001, TC-001)."""
```

---

## 8. `CLAUDE.md` — the agent's entry point

Every repo using this method has a `CLAUDE.md` at the root. It is small, factual, and points the agent at the spec layer. **It must not duplicate spec content** — only link to it.

Recommended minimal sections:

1. One-line project description
2. **Reference Material** — paths to authoritative specs (in-repo or external)
3. **Architecture** — link to design spec + ADR/ARCH index
4. **Tech Stack** — a table, no prose
5. **Commands** — exact `bash` invocations for test/lint/typecheck/run
6. **Project Structure** — annotated tree
7. **Conventions** — bullet list (commits, branches, TDD, type hints)
8. **Traceability IDs** — the table from §2 of this document

A template is in `templates/CLAUDE.md`.

---

## 9. What this method deliberately omits

- **Heavyweight architecture frameworks** (TOGAF, Zachman, full SysML) — overhead exceeds value for project-scale work.
- **TOSCA / declarative topology DSLs** — replaced by `ARCH-deployment.md` + `docker-compose.yml`.
- **Wiki tools** (Confluence, Notion) — Markdown in git is the source of truth. Anything else is a mirror.
- **Ticket-driven specs** — Jira/Linear tickets are work units, not specifications. Specs live in `docs/`.

---

## 10. Adoption checklist for a new project

- [ ] Create the `docs/` skeleton from §3.
- [ ] Copy the templates from this repo's `templates/` directory.
- [ ] Write `CLAUDE.md` from `templates/CLAUDE.md`.
- [ ] Seed `traceability.yaml` with at least one entry so the structure is non-empty.
- [ ] Add the traceability lint to CI (script provided in `templates/check_traceability.py`).
- [ ] Configure conventional-commits enforcement (`commitlint` or equivalent).
- [ ] Decide which `ARCH-*` views are needed for the project; create empty stubs only for the ones you'll actually populate.

---

## 11. Templates included

| File | Purpose |
|---|---|
| `templates/CLAUDE.md` | Agent entry point |
| `templates/REQ-functional.md` | Functional requirements doc |
| `templates/REQ-nonfunctional.md` | Non-functional requirements doc |
| `templates/REQ-testcases.md` | Test cases doc |
| `templates/ADR-template.md` | One ADR |
| `templates/ARCH-system-overview.md` | Context view |
| `templates/ARCH-data-model.md` | Data model view |
| `templates/ARCH-dataflow.md` | Runtime view |
| `templates/ARCH-deployment.md` | Deployment view |
| `templates/API-template.md` | API spec |
| `templates/UI-template.md` | UI spec |
| `templates/traceability.yaml` | Matrix scaffold |
| `templates/check_traceability.py` | CI linter |

---

## 12. Glossary

- **ADR** — Architecture Decision Record. One file, one decision, immutable once accepted.
- **arc42** — A pragmatic architecture documentation template (12 sections). This method uses a subset.
- **Traceability matrix** — A structured mapping requirement → downstream artifacts.
- **TDD** — Test-Driven Development. Failing test first, then implementation.
- **Conventional Commits** — `<type>(<scope>): <subject>` commit message format.
