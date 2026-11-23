"""Pont portable entre la compétence Agent Skills et le paquet METRO-MASTER."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


def _is_project_root(path: Path) -> bool:
    return (
        path.joinpath("pyproject.toml").is_file()
        and path.joinpath("src", "metro_master", "__init__.py").is_file()
    )


def _walk_roots(start: Path):
    yield start
    yield from start.parents


def _find_project_root(explicit: str | None) -> Path | None:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    configured = os.environ.get("METRO_MASTER_PROJECT_ROOT")
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.extend(_walk_roots(Path.cwd()))
    candidates.extend(_walk_roots(Path(__file__).resolve().parent))

    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if _is_project_root(resolved):
            return resolved
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--project-root")
    known, remaining = parser.parse_known_args(argv)

    root = _find_project_root(known.project_root)
    if root is not None:
        source = str(root / "src")
        if source not in sys.path:
            sys.path.insert(0, source)
        os.chdir(root)

    try:
        from metro_master.cli import main as metro_main
    except ImportError as error:
        raise SystemExit(
            "METRO-MASTER est introuvable. Installez le paquet Python, définissez "
            "METRO_MASTER_PROJECT_ROOT ou passez --project-root CHEMIN."
        ) from error
    return metro_main(remaining)


if __name__ == "__main__":
    raise SystemExit(main())
