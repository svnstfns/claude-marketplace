"""Traceability matrix linter.

Verifies that:
  1. Every REQ-F###/REQ-NF## declared in docs/requirements/ has an entry
     in docs/traceability.yaml.
  2. Every traceability entry with status `active` has at least one TC-### in `tests:`.
  3. Every traceability entry with status `dropped` has a `note:` and at least one ADR.
  4. Every path listed under `impl:` exists in the repo.
  5. Every ADR/ARCH/API/UI slug referenced in traceability.yaml resolves to a file.

Exit code 0 on success, 1 on any violation. Designed for CI.

Usage:
    python templates/check_traceability.py [--repo-root .]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("error: PyYAML is required (pip install pyyaml)\n")
    sys.exit(2)


REQ_PATTERN = re.compile(r"^### (REQ-(?:F|NF)\d{3}) ", re.MULTILINE)


def collect_req_ids(req_dir: Path) -> set[str]:
    ids: set[str] = set()
    for md in req_dir.glob("REQ-*.md"):
        ids.update(REQ_PATTERN.findall(md.read_text(encoding="utf-8")))
    return ids


def load_traceability(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise SystemExit("traceability.yaml must be a YAML list")
    return data


def resolve_slug(slug: str, search_dirs: list[Path]) -> Path | None:
    # `ARCH-foo#section` -> `ARCH-foo`
    base = slug.split("#", 1)[0]
    for d in search_dirs:
        candidate = d / f"{base}.md"
        if candidate.exists():
            return candidate
        # ADRs are typically named ADR-001-<slug>.md
        for f in d.glob(f"{base}-*.md"):
            return f
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".", type=Path)
    args = parser.parse_args()
    root: Path = args.repo_root.resolve()

    req_dir = root / "docs" / "requirements"
    arch_dir = root / "docs" / "architecture"
    api_dir = root / "docs" / "api"
    ui_dir = root / "docs" / "ui"
    matrix_path = root / "docs" / "traceability.yaml"

    if not matrix_path.exists():
        print(f"error: {matrix_path} not found", file=sys.stderr)
        return 1

    req_ids = collect_req_ids(req_dir)
    entries = load_traceability(matrix_path)

    errors: list[str] = []
    seen: set[str] = set()

    for entry in entries:
        req = entry.get("req")
        if not req:
            errors.append(f"entry without `req` key: {entry!r}")
            continue
        if req in seen:
            errors.append(f"duplicate entry for {req}")
        seen.add(req)

        status = entry.get("status", "active")
        if status == "active":
            tests = entry.get("tests") or []
            if not tests:
                errors.append(f"{req}: status=active but no tests linked")
        elif status == "dropped":
            if not entry.get("note"):
                errors.append(f"{req}: status=dropped without `note`")
            if not entry.get("adr"):
                errors.append(f"{req}: status=dropped without `adr` link")

        for path_str in entry.get("impl", []) or []:
            if not (root / path_str).exists():
                errors.append(f"{req}: impl path missing: {path_str}")

        for key, dirs in (
            ("arch", [arch_dir]),
            ("api", [api_dir]),
            ("ui", [ui_dir]),
            ("adr", [arch_dir]),
        ):
            for slug in entry.get(key, []) or []:
                if resolve_slug(slug, dirs) is None:
                    errors.append(f"{req}: {key} reference not found: {slug}")

    missing = req_ids - seen
    extra = seen - req_ids
    for r in sorted(missing):
        errors.append(f"{r}: defined in requirements but not in traceability.yaml")
    for r in sorted(extra):
        # extras are OK only if status=dropped (legacy IDs may not be in docs)
        if next((e for e in entries if e.get("req") == r), {}).get("status") != "dropped":
            errors.append(f"{r}: in traceability.yaml but not in requirements docs")

    if errors:
        for e in errors:
            print(f"FAIL  {e}", file=sys.stderr)
        print(f"\n{len(errors)} violation(s)", file=sys.stderr)
        return 1

    print(f"OK  {len(entries)} entries, {len(req_ids)} requirements, no violations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
