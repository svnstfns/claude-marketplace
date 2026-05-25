# docs-methodology

Lightweight, ID-anchored, arc42-inspired documentation methodology — bundled as a Claude Code skill with templates and a traceability linter.

## What it does

When you ask Claude to add a requirement, write an ADR, document an API, spec out a UI, or bootstrap `docs/` for a new project, this skill takes over. It:

- Allocates stable, immutable IDs (`REQ-F###`, `REQ-NF###`, `ADR-###`, `ARCH-<slug>`, `API-<slug>`, `UI-<slug>`, `TC-###`)
- Keeps the `docs/traceability.yaml` spine in sync with every change
- Uses the right template (Michael Nygard for ADRs, arc42 for architecture views) — bundled in `assets/templates/`
- Refuses to renumber IDs or to edit accepted ADRs (which would silently destroy audit trail)
- Provides a CI linter (`scripts/check_traceability.py`) that fails the build on broken links

## Install

Via the marketplace:

```bash
claude plugin install docs-methodology
```

Or copy the skill folder directly:

```bash
cp -r skills/documentation-methodology ~/.claude/skills/
```

## Use

Just talk to Claude normally. The skill triggers on phrases like:

- "Add a requirement for user registration with email confirmation"
- "Write an ADR for switching from SQLite to PostgreSQL"
- "Set up the docs structure for this new project"
- "Document the POST /feeds endpoint"

No need to invoke explicitly.

## Layout

```
skills/documentation-methodology/
├── SKILL.md                          # the skill itself
├── assets/templates/                 # ADR, REQ, ARCH, API, UI templates + CLAUDE.md template
├── references/METHODOLOGY.md         # full 12-section authoritative reference
└── scripts/check_traceability.py     # CI linter for docs/traceability.yaml
```

## Methodology

See [`skills/documentation-methodology/references/METHODOLOGY.md`](skills/documentation-methodology/references/METHODOLOGY.md) for the complete reference — philosophy, ID rules, workflows, conventions.
