# <Project Name>

<One-line project description.>

## Reference Material

- Requirements: `docs/requirements/`
- Architecture: `docs/architecture/` (ADR-001..N, ARCH-*)
- API specs: `docs/api/`
- UI specs: `docs/ui/`
- Research notes: `docs/research/`
- Traceability: `docs/traceability.yaml`

## Architecture

<Short prose: how many services, what each does, where the boundaries are.>

- [Design spec](docs/architecture/ARCH-system-overview.md)
- [ADR index](docs/architecture/)

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | <e.g. Python 3.11, FastAPI, SQLAlchemy 2.0> |
| Frontend | <e.g. React, TypeScript, Vite> |
| Database | <e.g. PostgreSQL 16> |
| Package manager | <e.g. uv (Python), pnpm (JS)> |

## Commands

```bash
# Tests
<test command>

# Lint
<lint command>

# Type check
<typecheck command>

# Run locally
<run command>
```

## Project Structure

```
<project-root>/
├─ docs/                    # all specifications (source of truth)
├─ src/                     # implementation
├─ tests/                   # unit + integration
└─ <other top-level dirs>
```

## Conventions

- Conventional Commits: `<type>(<scope>): <subject>`
- Branches: `<type>/<issue-or-id>-<description>`
- TDD: failing test (TC-###) before implementation
- Type hints / strict types on all public functions
- Schemas at every external boundary (Pydantic / Zod)
- async/await for I/O

## Traceability IDs

| Prefix | Scope | Example |
|--------|-------|---------|
| REQ-F### | Functional requirement | REQ-F010 |
| REQ-NF### | Non-functional requirement | REQ-NF003 |
| ADR-### | Architecture decision | ADR-002 |
| ARCH-* | Architecture view | ARCH-data-model |
| API-* | API spec | API-core-endpoints |
| UI-* | UI spec | UI-design-system |
| TC-### | Test case | TC-001 |

See `DOCUMENTATION-METHODOLOGY.md` for the full method.
