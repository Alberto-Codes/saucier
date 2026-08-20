"""Command line entry point.

Uses `argparse` rather than a CLI framework so that the package has no
runtime dependencies at all. A reader clones and runs, and nothing is
installed.

Three exit codes. Zero on success, `NOT_FOUND` when a lookup matches no
preparation, and `FAILED` when a source or a store could not be read.

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
import os
import sys
from collections.abc import Sequence

from saucier.domain.errors import SaucierError
from saucier.domain.models import Catalogue
from saucier.domain.types import ConceptId, to_concept_id
from saucier.infrastructure.bootstrap import catalogue_store, escoffier_source
from saucier.infrastructure.config import ESCOFFIER
from saucier.services.extraction import extract

BRANCH, LAST, PIPE, GAP = "├── ", "└── ", "│   ", "    "

NOT_FOUND = 1
"""Exit code when the catalogue holds no preparation under the given name."""

FAILED = 2
"""Exit code when a source or a store could not be read or written."""


def _parse(_: argparse.Namespace) -> int:
    """Extract the catalogue from the committed source and store it.

    Args:
        _: Parsed arguments, unused.

    Returns:
        Zero. Failures raise instead.
    """
    catalogue = extract(escoffier_source())
    written = catalogue_store().save(catalogue)

    print(f"source      {catalogue.source_id}")
    print(f"mothers     {', '.join(sorted(catalogue.mothers))}")
    print(f"sauces      {len(catalogue.preparations)}")
    print(f"derived     {catalogue.resolved} linked to a mother")
    print(f"unresolved  {catalogue.unresolved} state no base in their prose")
    print()
    print(f"Wrote {os.path.relpath(written)}")
    print("Those unresolved entries are the honest score. A parser cannot")
    print("read a derivation the source never wrote down.")
    return 0


def _tree(args: argparse.Namespace) -> int:
    """Print the derivation tree beneath one concept.

    Args:
        args: Parsed arguments carrying the root concept.

    Returns:
        Zero, or `NOT_FOUND` when nothing answers to the concept.
    """
    root = to_concept_id(args.concept)
    catalogue = catalogue_store().load(ESCOFFIER)
    found = catalogue.find(root)
    if found is None and root not in catalogue.mothers:
        print(f"no preparation named {args.concept!r}", file=sys.stderr)
        return NOT_FOUND

    # The bracket names the concept whose children follow, so a heading
    # drawn from a near match cannot pass itself off as the root.
    print(f"{found.title if found else args.concept}  [{root}]")
    _print_children(catalogue, root, prefix="", seen={root})
    return 0


def _print_children(
    catalogue: Catalogue, parent: ConceptId, prefix: str, seen: set[ConceptId]
) -> None:
    """Print one level of derivations, then recurse.

    Args:
        catalogue: The catalogue being walked.
        parent: Concept whose children to print.
        prefix: Indentation carried down from the parent.
        seen: Concepts already printed on this branch, so a cycle in the
            recorded parents cannot recurse without end.
    """
    children = catalogue.children_of(parent)
    for position, child in enumerate(children):
        final = position == len(children) - 1
        languages = "/".join(sorted({t.language.value for t in child.terms}))
        print(f"{prefix}{LAST if final else BRANCH}{child.title}  ({languages})")
        if child.concept not in seen:
            _print_children(
                catalogue,
                child.concept,
                prefix + (GAP if final else PIPE),
                seen | {child.concept},
            )


def _show(args: argparse.Namespace) -> int:
    """Print one preparation in full.

    Args:
        args: Parsed arguments carrying the concept to show.

    Returns:
        Zero, or `NOT_FOUND` when nothing answers to the concept.
    """
    concept = to_concept_id(args.concept)
    matches = catalogue_store().load(ESCOFFIER).matches(concept)
    if not matches:
        print(f"no preparation named {args.concept!r}", file=sys.stderr)
        return NOT_FOUND

    preparation = matches[0]
    print(preparation.title)
    print(f"entry {preparation.ref.entry}, line {preparation.ref.line}")
    for term in preparation.terms:
        print(f"  term  {term.surface}  [{term.language.value}]  {term.concept}")
    print(
        f"  parent  {'(unresolved)' if preparation.parent is None else preparation.parent}"
    )
    print()
    print(_prose(preparation.body, args.chars))
    if len(matches) > 1:
        others = ", ".join(p.title for p in matches[1:])
        print(f"\nAlso matching {args.concept!r}: {others}", file=sys.stderr)
    return 0


def _prose(body: str, limit: int) -> str:
    """Cut the prose to length, saying so when anything was cut.

    Args:
        body: The entry's prose.
        limit: How many characters to print.

    Returns:
        The prose, with a note when it was truncated.
    """
    if len(body) <= limit:
        return body
    return f"{body[:limit]}...\n[{len(body) - limit} more characters, raise --chars to read them]"


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
        Zero on success, `NOT_FOUND` when a lookup misses, `FAILED` when a
        source or store could not be read or written.
    """
    args = build_parser().parse_args(argv)
    try:
        return int(args.run(args))
    except SaucierError as exc:
        print(f"saucier: {exc}", file=sys.stderr)
        return FAILED


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
