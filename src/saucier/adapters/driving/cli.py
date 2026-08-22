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
    - [saucier.services.comparison][]: What `diff` calls into.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from saucier.domain.errors import SaucierError
from saucier.domain.models import Catalogue
from saucier.domain.types import ConceptId, to_concept_id
from saucier.infrastructure.bootstrap import (
    catalogue_store,
    default_source_id,
    escoffier_sources,
)
from saucier.services.comparison import Difference, Report, compare
from saucier.services.extraction import extract

BRANCH, LAST, PIPE, GAP = "├── ", "└── ", "│   ", "    "

INDENT = " " * 16
"""Census lines sit under the source id, which is 14 characters plus a gap."""

NOT_FOUND = 1
"""Exit code when the catalogue holds no preparation under the given name."""

FAILED = 2
"""Exit code when a source or a store could not be read or written."""


def _parse(_: argparse.Namespace) -> int:
    """Extract every committed witness and store each catalogue.

    Prints one block per witness: the edition the document states, how the
    text was obtained, the mothers the source names, and the census.

    Args:
        _: Parsed arguments, unused.

    Returns:
        Zero. Failures raise instead.
    """
    written = []
    for source in escoffier_sources():
        catalogue = extract(source)
        written.append(catalogue_store().save(catalogue))
        witness, edition = catalogue.witness, catalogue.witness.edition
        impression = (
            f" (impression: {edition.impression})" if edition.impression else ""
        )
        stated = edition.statement or f"no edition stated, copyright {edition.year}"
        print(f"{witness.source_id:<14}  {stated}{impression}")
        print(f"{INDENT}{witness.fidelity.value} of {witness.origin}")
        print(f"{INDENT}mothers: {', '.join(sorted(catalogue.mothers))}")
        print(
            f"{INDENT}{len(catalogue.preparations)} sauces, "
            f"{catalogue.resolved} derived, {catalogue.unresolved} unresolved"
        )
    print()
    for path in written:
        print(f"Wrote {os.path.relpath(path)}")
    print("Those unresolved entries are the honest score. A parser cannot")
    print("read a derivation the source never wrote down.")
    return 0


def _diff(args: argparse.Namespace) -> int:
    """Compare two stored catalogues and print what caused each difference.

    Args:
        args: Parsed arguments carrying the two source ids.

    Returns:
        Zero. Failures raise instead.
    """
    store = catalogue_store()
    report = compare(store.load(args.older), store.load(args.newer))
    print(f"{report.older}  ->  {report.newer}")
    _print_rows(report, "names", report.presence)
    _print_rows(report, "parents", report.parents)
    print()
    print("  " + ", ".join(f"{n} {c.value}" for c, n in report.tally().items()))
    print("  No row is adjudicated. An ocr-suspected row is a suspicion, and")
    print("  separating a scan artefact from a revision needs both lines read.")
    return 0


def _print_rows(report: Report, heading: str, rows: Sequence[Difference]) -> None:
    """Print one section of a comparison.

    Args:
        report: The comparison being printed, for its column headings.
        heading: What the section compares.
        rows: The differences to print, already ordered.
    """
    print()
    print(f"{heading}  ({len(rows)})")
    print(f"  {'cause':<30}  {'concept':<34}  {report.older} / {report.newer}")
    for row in rows:
        causes = ", ".join(cause.value for cause in row.causes)
        pair = f"{row.concept} ~ {row.counterpart}" if row.counterpart else row.concept
        print(f"  {causes:<30}  {pair:<34}  {_side(row.older)} / {_side(row.newer)}")
        print(f"  {'':<30}  {'':<34}  {row.note}")


def _side(value: str | None) -> str:
    """Render what one witness holds for a compared field.

    Args:
        value: The recorded title or parent, or None.

    Returns:
        The value, or a marker for an absent or unresolved one.
    """
    return "(none)" if value is None else value


def _tree(args: argparse.Namespace) -> int:
    """Print the derivation tree beneath one concept.

    Args:
        args: Parsed arguments carrying the root concept and the source.

    Returns:
        Zero, or `NOT_FOUND` when nothing answers to the concept.
    """
    root = to_concept_id(args.concept)
    catalogue = catalogue_store().load(args.source or default_source_id())
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
        args: Parsed arguments carrying the concept to show and the source.

    Returns:
        Zero, or `NOT_FOUND` when nothing answers to the concept.
    """
    concept = to_concept_id(args.concept)
    store = catalogue_store()
    matches = store.load(args.source or default_source_id()).matches(concept)
    if not matches:
        print(f"no preparation named {args.concept!r}", file=sys.stderr)
        return NOT_FOUND

    preparation = matches[0]
    ref = preparation.ref
    print(preparation.title)
    print(
        f"entry {ref.entry}, line {ref.line}, {ref.fidelity.value} of {ref.source_id}"
    )
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

    The tree command roots at any preparation, not only a mother. A lookup
    reads the first committed witness unless `--source` names another.

    Returns:
        The configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="saucier",
        description="Extract sauce preparations from a source, deterministically.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("parse", help="extract every witness and store it").set_defaults(
        run=_parse
    )

    tree = sub.add_parser("tree", help="print the derivations beneath a concept")
    tree.add_argument("concept", help="the root preparation, e.g. bordelaise")
    _add_source(tree)
    tree.set_defaults(run=_tree)

    show = sub.add_parser("show", help="print one preparation in full")
    show.add_argument("concept", help="a preparation, e.g. bordelaise")
    show.add_argument("--chars", type=int, default=600, help="prose to print")
    _add_source(show)
    show.set_defaults(run=_show)

    diff = sub.add_parser("diff", help="compare two stored catalogues")
    diff.add_argument("older", help="the earlier edition, e.g. escoffier-1907")
    diff.add_argument("newer", help="the later edition, e.g. escoffier-1909")
    diff.set_defaults(run=_diff)
    return parser


def _add_source(command: argparse.ArgumentParser) -> None:
    """Give one command the option that chooses a witness.

    Args:
        command: The subparser to extend.
    """
    command.add_argument(
        "--source",
        default=None,
        help="source id to read, e.g. escoffier-1907 (default: the revision)",
    )


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
