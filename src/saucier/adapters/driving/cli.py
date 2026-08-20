"""Command line entry point.

Uses `argparse` rather than a CLI framework so that the package has no
runtime dependencies at all. A reader clones and runs; nothing is installed.

Examples:
    Drive the interface in process:

    ```python
    from saucier.adapters.driving.cli import main

    assert main(["parse"]) == 0
    assert main(["tree", "espagnole"]) == 0
    ```

See Also:
    - [saucier.services.extraction][]: What these commands call into.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from saucier.domain.errors import SaucierError
from saucier.domain.models import Catalogue
from saucier.domain.types import ConceptId, to_concept_id
from saucier.infrastructure.bootstrap import catalogue_store, escoffier_source
from saucier.infrastructure.config import ESCOFFIER
from saucier.services.extraction import extract

BRANCH, LAST, PIPE, GAP = "├── ", "└── ", "│   ", "    "


def _parse(_: argparse.Namespace) -> int:
    """Extract the catalogue from the committed source and store it.

    Args:
        _: Parsed arguments, unused.

    Returns:
        Process exit code.
    """
    catalogue = extract(escoffier_source())
    catalogue_store().save(catalogue)

    total = len(catalogue.preparations)
    unresolved = total - catalogue.resolved
    print(f"source      {catalogue.source_id}")
    print(f"mothers     {', '.join(sorted(catalogue.mothers))}")
    print(f"sauces      {total}")
    print(f"derived     {catalogue.resolved} linked to a mother")
    print(f"unresolved  {unresolved} state no base in their prose")
    print()
    print(f"Wrote data/{catalogue.source_id}.json")
    print("Those unresolved entries are the honest score. A parser cannot")
    print("read a derivation the source never wrote down.")
    return 0


def _tree(args: argparse.Namespace) -> int:
    """Print the derivation tree beneath one concept.

    Args:
        args: Parsed arguments carrying the root concept.

    Returns:
        Process exit code.
    """
    catalogue = catalogue_store().load(ESCOFFIER)
    root = to_concept_id(args.concept)
    found = catalogue.find(root)
    if found is None and root not in catalogue.mothers:
        print(f"no preparation named {args.concept!r}", file=sys.stderr)
        return 1

    heading = found.title if found else args.concept
    print(f"{heading}  [{root}]")
    _print_children(catalogue, root, prefix="")
    return 0


def _print_children(catalogue: Catalogue, parent: ConceptId, prefix: str) -> None:
    """Print one level of derivations, then recurse.

    Args:
        catalogue: The catalogue being walked.
        parent: Concept whose children to print.
        prefix: Indentation carried down from the parent.
    """
    children = catalogue.children_of(parent)
    for position, child in enumerate(children):
        final = position == len(children) - 1
        languages = "/".join(sorted({t.language.value for t in child.terms}))
        print(f"{prefix}{LAST if final else BRANCH}{child.title}  ({languages})")
        _print_children(catalogue, child.concept, prefix + (GAP if final else PIPE))


def _show(args: argparse.Namespace) -> int:
    """Print one preparation in full.

    Args:
        args: Parsed arguments carrying the concept to show.

    Returns:
        Process exit code.
    """
    catalogue = catalogue_store().load(ESCOFFIER)
    preparation = catalogue.find(to_concept_id(args.concept))
    if preparation is None:
        print(f"no preparation named {args.concept!r}", file=sys.stderr)
        return 1

    print(preparation.title)
    print(f"entry {preparation.ref.entry}, line {preparation.ref.line}")
    for term in preparation.terms:
        print(f"  term  {term.surface}  [{term.language.value}]  {term.concept}")
    print(f"  parent  {preparation.parent or '(unresolved)'}")
    print()
    print(preparation.body[: args.chars])
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Define the command line interface.

    Returns:
        The configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="saucier",
        description="Extract sauce preparations from a source, deterministically.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("parse", help="extract the catalogue and store it").set_defaults(
        run=_parse
    )

    tree = sub.add_parser("tree", help="print the derivations beneath a concept")
    tree.add_argument("concept", help="a mother sauce, e.g. espagnole")
    tree.set_defaults(run=_tree)

    show = sub.add_parser("show", help="print one preparation in full")
    show.add_argument("concept", help="a preparation, e.g. bordelaise")
    show.add_argument("--chars", type=int, default=600, help="prose to print")
    show.set_defaults(run=_show)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line interface.

    Args:
        argv: Arguments to parse, taken from the process when omitted.

    Returns:
        Process exit code.
    """
    args = build_parser().parse_args(argv)
    try:
        return int(args.run(args))
    except SaucierError as exc:
        print(f"saucier: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
