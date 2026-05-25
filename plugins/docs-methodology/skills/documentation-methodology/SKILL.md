---
name: documentation-methodology
description: Apply a lightweight, ID-anchored, arc42-inspired documentation methodology when working on project documentation. Use this skill whenever the user adds, edits, audits, or sets up specifications — functional requirements (REQ-F), non-functional requirements (REQ-NF), architecture decision records (ADRs), architecture views (ARCH-*), API specs, UI specs, or test cases (TC). Trigger on phrases like "add requirement", "write an ADR", "document the API", "spec out", "design doc", "architecture decision", "traceability", "arc42", or whenever the user touches anything under docs/requirements/, docs/architecture/, docs/api/, docs/ui/, or docs/traceability.yaml. Also trigger when bootstrapping a new project's docs/ folder. The skill enforces stable IDs, immutable accepted ADRs, the traceability.yaml spine, and the right template for each artifact. Use it even when the user does not name the methodology explicitly — any "let's document X" or "I need to capture this decision" intent is a hit.
---

# Documentation Methodology

A lightweight, arc42-inspired, ID-anchored specification method for software projects. Every spec lives as plain Markdown + YAML under `docs/`, every artifact has a stable ID, and `docs/traceability.yaml` is the spine that links Requirement → Architecture → API → UI → Test → Implementation.

Use this skill in two modes — it picks the right one automatically based on whether `docs/` already exists.

---

## Decide which mode you are in

Before doing anything else, check the working directory:

```bash
test -d docs && test -f docs/traceability.yaml && echo "EDIT" || echo "SETUP"
```

- **SETUP mode** — `docs/` or `docs/traceability.yaml` is missing. Bootstrap the structure before writing any spec.
- **EDIT mode** — the structure is in place. Add or modify a single artifact, then update the spine.

If only some of the structure is present (partial bootstrap), treat the missing pieces as SETUP for those specific files but do not overwrite anything that already exists.

---

## SETUP mode — bootstrap a new project

When `docs/` is missing or incomplete, scaffold it from the bundled templates. The templates live next to this skill at `assets/templates/`.

### Steps

1. **Create the directory skeleton** at the repo root:
   ```
   docs/
   ├─ requirements/
   ├─ architecture/
   ├─ api/
   ├─ ui/
   ├─ research/
   └─ traceability.yaml
   ```

2. **Copy templates** from `assets/templates/`. They split into three buckets — handle each differently:

   **Bucket A — Copy verbatim, no edits:**
   - `REQ-functional.md` → `docs/requirements/REQ-functional.md`
   - `REQ-nonfunctional.md` → `docs/requirements/REQ-nonfunctional.md`
   - `REQ-testcases.md` → `docs/requirements/REQ-testcases.md`
   - `scripts/check_traceability.py` → repo `scripts/check_traceability.py`

   The REQ/TC templates ship with one or two illustrative placeholder entries (`REQ-F001 — <Short imperative title>` etc.). Leave those as-is; they are scaffolding the user will overwrite or extend when adding the first real REQ. They are NOT placeholders you should fill in during setup.

   **Bucket B — Copy and fill placeholders from the conversation:**
   - `CLAUDE.md` → repo root `CLAUDE.md` (only if none exists)
   - `docs/traceability.yaml` ← derived from `assets/templates/traceability.yaml`, but seeded with a real first entry (see step 3)

   For `CLAUDE.md`: do not ship `<Project Name>`, `<Short prose>`, `<test command>`, `<e.g. uv>`, or any other `<...>` placeholder back to the user. Replace every angle-bracket placeholder with information from the conversation (project name, one-line description, tech stack, common commands if you know them). If a value is genuinely unknown, write `TBD` rather than leaving the angle brackets. The agent's entry point should be usable as-is the moment setup finishes — placeholders that survive into the committed file create friction every time someone reads it.

   **Bucket C — Create only what the project actually needs:**
   - `ARCH-system-overview.md`, `ARCH-data-model.md`, `ARCH-dataflow.md`, `ARCH-deployment.md` → `docs/architecture/`
   - `API-template.md` → `docs/api/API-<slug>.md`
   - `UI-template.md` → `docs/ui/UI-<slug>.md`

   Do NOT copy these as empty stubs by default. Pick only the ones you can populate now with real project content drawn from the conversation. A typical greenfield setup gets `ARCH-system-overview.md` (because you usually know roughly what the system is for) and maybe `ARCH-deployment.md` (if the tech stack already implies a topology). Skip the rest — they'll be created later when there's content to put in them. An empty `ARCH-data-model.md` with a `<EntityName>` placeholder is worse than no file: it rots, it lies, and the next reader has to wade through scaffolding to find real content.

   API and UI files are slug-named, so they only exist when there's an actual API surface or UI screen to specify. Skip during initial setup unless explicitly relevant.

3. **Do not** copy `ADR-template.md` to a fixed location. ADRs are created on demand as `docs/architecture/ADR-NNN-<slug>.md`, one per file.

4. **Seed `docs/traceability.yaml`** with at least one realistic entry derived from the conversation so the structure is non-empty. The seed should match a real capability the user mentioned (e.g. for a feed crawler: `REQ-F001 — Register an RSS feed source`). Do not commit the bare template content with placeholder REQs.

5. **Briefly tell the user** what was created (one line per file) and what the next concrete step is — typically "open `docs/requirements/REQ-functional.md` and replace the `REQ-F001 — <Short imperative title>` scaffold with your first real requirement". Do not dump file contents back at them.

---

## EDIT mode — adding or changing one artifact

This is the most common case. The user wants to capture something: a new requirement, a decision, an API endpoint, a UI screen, a test case, or a change to an existing entry. Follow the workflow for the artifact type.

### 1. Identify what kind of artifact

Pick the right template and target file:

| The user wants to capture… | Prefix | Template | Target file |
|---|---|---|---|
| A capability the system must provide | `REQ-F###` | (append to) `REQ-functional.md` | `docs/requirements/REQ-functional.md` |
| A quality attribute with a measurable scenario | `REQ-NF###` | (append to) `REQ-nonfunctional.md` | `docs/requirements/REQ-nonfunctional.md` |
| An architectural choice with consequences | `ADR-###` | `assets/templates/ADR-template.md` | `docs/architecture/ADR-NNN-<slug>.md` (new file) |
| A view of the architecture (data, runtime, deployment, context) | `ARCH-<slug>` | corresponding ARCH template | `docs/architecture/ARCH-<slug>.md` |
| An API surface | `API-<slug>` | `assets/templates/API-template.md` | `docs/api/API-<slug>.md` |
| A UI/UX surface | `UI-<slug>` | `assets/templates/UI-template.md` | `docs/ui/UI-<slug>.md` |
| A test scenario | `TC-###` | (append to) `REQ-testcases.md` | `docs/requirements/REQ-testcases.md` |

### 2. Allocate the next ID

IDs are immutable, sequential, and zero-padded. Never renumber. To find the next number for a counted prefix:

```bash
grep -oE '^### (REQ-F|REQ-NF|TC-)[0-9]{3}' docs/requirements/*.md | sort -u
ls docs/architecture/ADR-*.md 2>/dev/null
```

Take the highest existing number + 1, pad to 3 digits. For `<slug>`-style IDs (`ARCH-`, `API-`, `UI-`), the slug is descriptive kebab-case, not a number.

### 3. Fill in the template

Read the matching template from `assets/templates/` and produce the new entry. Hard rules per artifact:

- **REQ-F###** — atomic, testable, active voice. Must have at least one acceptance criterion and at least one linked `TC-###`. If you don't have a test case yet, write one now.
- **REQ-NF###** — must include a measurable scenario (numbers or thresholds). Vague adjectives like "fast" or "secure" without a number are rejected.
- **ADR-###** — Michael Nygard format. New ADRs start as `Status: proposed`. Once `accepted`, the file is **immutable**: a later change requires a new ADR that supersedes this one (set the old one's `Superseded by:` and the new one's `Supersedes:`). Never edit an accepted ADR's Context/Decision/Consequences.
- **ARCH-\*** — living documents, may be edited freely. But a change that flips a recorded decision requires a new ADR first; only then update the ARCH view.
- **API-\* / UI-\*** — every endpoint or screen should reference the `REQ-F###` it implements via a `Verifies:` line.
- **TC-###** — must reference at least one `REQ-F###` or `REQ-NF###` via `Verifies:` and point at an executable test path via `Impl:`.

### 4. Update `docs/traceability.yaml`

This is non-optional. Every REQ has exactly one entry; every change to an artifact must reflect into the spine.

- New REQ → add an entry with `status: active`, populated `tests:`, and the linked `arch/api/ui` slugs (if known yet).
- Dropping a REQ → set `status: dropped`, add `note:` explaining why, and an `adr:` link to the supersession.
- New ADR that supersedes a decision → add `note:` and `adr:` to affected REQ entries.
- New API/UI/ARCH → if it implements a tracked REQ, add the slug to that REQ's entry.

Schema example:
```yaml
- req: REQ-F001
  title: Create crawl source
  status: active                   # active | deferred | dropped
  arch: [ARCH-data-model]
  api: [API-core-endpoints#POST-sources]
  ui: [UI-sources#create-form]
  tests: [TC-001]
  impl:
    - src/api/routes/sources.py
```

### 5. Verify (optional but recommended)

If the project has Python available, run the bundled linter to catch broken links:

```bash
python scripts/check_traceability.py --repo-root .
```

Or copy `scripts/check_traceability.py` from this skill into the project under `scripts/` or `docs/`. It exits non-zero on any violation (missing entry, broken slug, missing impl path, dropped REQ without ADR link).

### 6. Tell the user, concisely

State: which file changed, which ID was allocated, what's still needed (e.g., "TC-007 has no `Impl:` path yet — point it at the test function when you've written it"). Do not echo the whole file back.

---

## ID system at a glance

| Prefix | Scope | Example |
|---|---|---|
| `REQ-F###` | Functional requirement | `REQ-F010` |
| `REQ-NF###` | Non-functional requirement | `REQ-NF003` |
| `ADR-###` | Architecture decision | `ADR-002` |
| `ARCH-<slug>` | Architecture view | `ARCH-data-model` |
| `API-<slug>` | API spec | `API-core-endpoints` |
| `UI-<slug>` | UI spec | `UI-design-system` |
| `TC-###` | Test case | `TC-001` |

**Iron rules:**
- IDs are immutable. Never rename. Dropping a REQ uses `status: dropped`, never deletion.
- One ADR per file. Accepted ADRs are immutable.
- Numbers are assigned in creation order. Never reordered, never reused.

---

## Common pitfalls — avoid these

These are the failure modes the methodology is designed to prevent:

- **"Let me just update the ADR" on an accepted ADR.** No — write a new ADR that supersedes it. The audit trail is the point.
- **Renumbering IDs for tidiness.** Never. `REQ-F042` stays `REQ-F042` even if `REQ-F001..F041` are all dropped.
- **Adding a REQ without a test case.** A REQ with no `TC-###` is incomplete; either write a test case immediately or mark the REQ `deferred`.
- **Vague non-functional requirements.** "The system must be fast" is not a REQ-NF. "Search returns top-10 results in <500ms at p95 over 100k chunks on 8 vCPU / 16GB RAM" is.
- **Editing `traceability.yaml` by accident-of-omission.** Every change to an artifact should propagate to the spine in the same commit.
- **Empty `ARCH-*` stub files.** Only create the views you're going to populate. Stubs rot.
- **Spec in code comments.** Specs live in `docs/`. Code comments may reference IDs but never replace them.

---

## When to consult the full reference

For background on the philosophy, full artifact specifications, workflow details, glossary, or anything you're unsure about, read `references/METHODOLOGY.md` (the full 12-section authoritative method). Use it for:

- Detailed examples of each artifact type
- The complete workflow for changing a decision or dropping a requirement
- Commit/branch conventions tied to the IDs
- What this method deliberately omits and why

---

## Bundled assets

- `assets/templates/` — every template referenced above. Copy-paste from these; do not rewrite from memory.
- `scripts/check_traceability.py` — CI linter for the spine.
- `references/METHODOLOGY.md` — full authoritative reference (read when in doubt).
