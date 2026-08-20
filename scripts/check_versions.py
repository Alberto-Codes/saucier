"""Version-sync gate: every recorded version agrees.

The project version is written in four places. release-please updates
`pyproject.toml`, the manifest, and the annotated `__version__`. A separate
CI job updates `uv.lock`. Any one of those can silently fall behind, and the
symptom appears far from the cause: a stale lockfile fails `uv lock --check`
on the release PR and reads as a dependency problem.

This gate fails the moment they disagree.

Examples:
    Run against the tree:

    ```console
    $ uv run python scripts/check_versions.py
    all four agree on 0.0.1
    ```
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _pyproject() -> str:
    """Read the version declared in `pyproject.toml`.

    Returns:
        The declared version string.
    """
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _dunder() -> str:
    """Read `__version__` from the package.

    Returns:
        The version string, or an empty string when absent.
    """
    text = (ROOT / "src" / "saucier" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    return match.group(1) if match else ""


def _manifest() -> str:
    """Read the version release-please last released.

    Returns:
        The version string, or an empty string when absent.
    """
    data = json.loads((ROOT / ".release-please-manifest.json").read_text())
    return str(data.get(".", ""))


def _lockfile() -> str:
    """Read the project version recorded in `uv.lock`.

    Returns:
        The version string, or an empty string when absent.
    """
    text = (ROOT / "uv.lock").read_text(encoding="utf-8")
    match = re.search(r'name = "saucier"\nversion = "([^"]+)"', text)
    return match.group(1) if match else ""


def main() -> int:
    """Compare every recorded version.

    Returns:
        Process exit code: 0 when all agree, 1 otherwise.
    """
    found = {
        "pyproject.toml": _pyproject(),
        "src/saucier/__init__.py": _dunder(),
        ".release-please-manifest.json": _manifest(),
        "uv.lock": _lockfile(),
    }
    distinct = set(found.values())
    if len(distinct) == 1 and "" not in distinct:
        print(f"all four agree on {distinct.pop()}")
        return 0
    for where, version in sorted(found.items()):
        print(f"FAIL {where}: {version or '(not found)'}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
