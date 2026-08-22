"""Census gate: the published counts match what the parser prints.

Four pages and one stylesheet quote the number of sauces, the number linked
to a stated parent, and the number left unresolved. Those numbers are the
project's headline claim, and nothing about a stale one looks wrong on the
page.

The corpus holds two witnesses, so the gate runs both. The 1909 revision is
the one two published posts quote, and it carries the whole surface list.
The 1907 first printing is quoted on fewer pages, and every page that quotes
it is checked too.

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

from saucier.domain.models import Catalogue  # noqa: E402
from saucier.infrastructure.bootstrap import escoffier_sources  # noqa: E402
from saucier.services.extraction import extract  # noqa: E402


def census_line(catalogue: Catalogue) -> str:
    """Build the line `saucier parse` prints for one witness.

    Args:
        catalogue: The catalogue just extracted.

    Returns:
        The census exactly as the command reports it.
    """
    return (
        f"{len(catalogue.preparations)} sauces, "
        f"{catalogue.resolved} derived, {catalogue.unresolved} unresolved"
    )


def quoted(revision: Catalogue, first: Catalogue) -> dict[str, tuple[str, ...]]:
    """Build the strings each surface has to carry.

    Args:
        revision: The 1909 revision, whose census the posts quote.
        first: The 1907 first printing.

    Returns:
        A mapping from path to the strings that path must contain.
    """
    sauces = len(revision.preparations)
    derived, unresolved = revision.resolved, revision.unresolved
    both = (census_line(revision), census_line(first))
    return {
        "README.md": (*both, f"## The interesting number is {unresolved}"),
        "docs/index.md": (
            *both,
            f"<b>{sauces}</b> preparations",
            f"<b>{derived}</b> resolved",
            f"<b>{unresolved}</b> unresolved",
            (
                f"Of {sauces} preparations, {derived} resolve to a stated "
                f"parent and {unresolved} are unresolved."
            ),
        ),
        "docs/tutorial/first-run.md": (
            *both,
            f"**{sauces} sauces**",
            f"**{unresolved} unresolved**",
        ),
        "docs/reference/data-model.md": (
            f"{sauces} preparations<br/>{unresolved} unresolved",
            f"Catalogue of {sauces}",
            f"`Catalogue` of {sauces} preparations. {derived} resolve to a stated parent",
        ),
        "docs/reference/cli.md": both,
        # The bar is drawn from flex ratios, so it lies silently when the
        # split moves and nobody redraws it.
        "docs/stylesheets/theme.css": (f"flex: {derived};", f"flex: {unresolved};"),
    }


def main() -> int:
    """Compare every quoted count against the parser.

    Returns:
        Process exit code: 0 when every surface agrees, 1 otherwise.
    """
    revision, first = (extract(source) for source in escoffier_sources())
    wanted = quoted(revision, first)

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
