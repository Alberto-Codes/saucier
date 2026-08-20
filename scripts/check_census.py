"""Census gate: the published counts match what the parser prints.

Four pages and one stylesheet quote the number of sauces, the number linked
to a mother, and the number left unresolved. Those numbers are the project's
headline claim, and nothing about a stale one looks wrong on the page.

`tests/conftest.py` pins the counts, so a parser change fails the suite. It
does not prove anybody then updated the prose. This gate runs the parser and
looks for the numbers it printed. A count inside a mermaid block is checked
too, which the prose gate cannot do, because it skips fenced code.

Examples:
    Run against the tree:

    ```console
    $ uv run python scripts/check_census.py
    checked N quoted counts across M surfaces
    ```
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from saucier.infrastructure.bootstrap import escoffier_source  # noqa: E402
from saucier.services.extraction import extract  # noqa: E402


def quoted(sauces: int, derived: int, unresolved: int) -> dict[str, tuple[str, ...]]:
    """Build the strings each surface has to carry.

    Args:
        sauces: Preparations in the catalogue.
        derived: Preparations linked to a stated parent.
        unresolved: Preparations stating no base.

    Returns:
        A mapping from path to the strings that path must contain.
    """
    census = (
        f"sauces      {sauces}",
        f"derived     {derived} linked to a stated parent",
        f"unresolved  {unresolved} state no base in their prose",
    )
    return {
        "README.md": (*census, f"## The interesting number is {unresolved}"),
        "docs/index.md": (
            *census,
            f"<b>{sauces}</b> preparations",
            f"<b>{derived}</b> resolved",
            f"<b>{unresolved}</b> unresolved",
            (
                f"Of {sauces} preparations, {derived} resolve to a stated "
                f"parent and {unresolved} are unresolved."
            ),
        ),
        "docs/tutorial/first-run.md": (
            *census,
            f"**{sauces} sauces**",
            f"**{unresolved} unresolved**",
        ),
        "docs/reference/data-model.md": (
            f"{sauces} preparations<br/>{unresolved} unresolved",
            f"Catalogue of {sauces}",
            f"`Catalogue` of {sauces} preparations. {derived} resolve to a stated parent",
        ),
        # The bar is drawn from flex ratios, so it lies silently when the
        # split moves and nobody redraws it.
        "docs/stylesheets/theme.css": (f"flex: {derived};", f"flex: {unresolved};"),
    }


def main() -> int:
    """Compare every quoted count against the parser.

    Returns:
        Process exit code: 0 when every surface agrees, 1 otherwise.
    """
    catalogue = extract(escoffier_source())
    wanted = quoted(
        len(catalogue.preparations), catalogue.resolved, catalogue.unresolved
    )

    failed = False
    checked = 0
    for name, strings in sorted(wanted.items()):
        path = ROOT / name
        if not path.is_file():
            # A gate that scans nothing must fail loudly, not pass silently —
            # a renamed page would otherwise disable it.
            print(f"FAIL {name}: not found")
            failed = True
            continue
        text = path.read_text(encoding="utf-8")
        for string in strings:
            checked += 1
            if string not in text:
                print(f"FAIL {name}: does not quote {string!r}")
                failed = True
    print(f"checked {checked} quoted counts across {len(wanted)} surfaces")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
