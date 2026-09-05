"""Command line entry point.

Uses `argparse` rather than a CLI framework so that the package has no
runtime dependencies at all. A reader clones and runs, and nothing is
installed.

Three exit codes. Zero on success, `NOT_FOUND` when a lookup matches no
preparation, and `FAILED` when a source or a store could not be read.

The `diff` command prints how much of each witness the reader could see,
beside the counts rather than below them, because a count read without its
blind spot is a stronger claim than the evidence carries.

The `show` command prints the candidates an unresolved parent states, so a
refusal is readable beside the sentence that caused it. It prints the
procedure recorded for the preparation, one operation per line, after
the service has checked every word of it against the body. A preparation
with none recorded says so. The `tree` command names the root's own
parent on its heading line, because a mother that states a roux is not a
root.

The `export` command writes every stored catalogue to standard output as the
interchange and nothing else, so the stream can be piped. The `import`
command reads the interchange from standard input, rebuilds every catalogue
in memory, and prints the census. Its `--check` flag is mandatory, because
the command writes nothing and the verb must not suggest otherwise. A
stream that carries no catalogue is a failure, because that is what a
failed export leaves on the other side of a pipe. Both commands own the
encoding of their streams, because the interchange is UTF-8 by contract
and the locale is not consulted.

Every command prints to standard output, so a reader that closes the pipe
early is handled once, in `main`, and every command exits clean.

Examples:
    Drive the interface in process:

    ```python
    from saucier.adapters.driving.cli import main

    assert main(["parse"]) == 0
    assert main(["tree", "espagnole"]) == 0
    assert main(["export"]) == 0
    ```

See Also:
    - [saucier.services.extraction][]: What these commands call into.
    - [saucier.services.comparison][]: What `diff` calls into.
    - [saucier.ports.interchange][]: What `export` and `import` call into.
    - [saucier.services.procedure][]: What `show` calls into for a procedure.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Iterable, Sequence
from typing import TextIO

from saucier.domain.errors import InterchangeEmpty, SaucierError
from saucier.domain.models import Catalogue, Preparation
from saucier.domain.procedure import Input, Operation, Parameter, Procedure
from saucier.domain.types import ConceptId, to_concept_id
from saucier.infrastructure.bootstrap import (
    catalogue_interchange,
    catalogue_store,
    default_source_id,
    escoffier_sources,
    recorded_procedures,
)
from saucier.services.comparison import Difference, Report, compare
from saucier.services.extraction import (
    extract,
    own_names,
    parent_candidates,
    stated_candidates,
)
from saucier.services.procedure import procedure_of

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


def _export(_: argparse.Namespace) -> int:
    """Write every stored catalogue to standard output as the interchange.

    Every catalogue is loaded before the first line is written, so a
    missing one is reported on standard error and standard output stays
    empty. Nothing but records reaches standard output.

    The catalogues are the ones of the configured witnesses, and each
    witness reads its own id from the corpus front matter. So the command
    reads the corpus for the ids and the store for the catalogues.

    Args:
        _: Parsed arguments, unused.

    Returns:
        Zero. A catalogue that cannot be loaded raises instead.
    """
    store = catalogue_store()
    catalogues = [store.load(s.witness.source_id) for s in escoffier_sources()]
    _utf8(sys.stdout)
    sys.stdout.writelines(catalogue_interchange().encode(catalogues))
    return 0


def _utf8(stream: object) -> None:
    """Make a standard stream carry UTF-8 whatever the locale says.

    The interchange is UTF-8 by contract. Left to the locale, an export
    under latin-1 would die on the first em dash after writing two lines,
    and an import under UTF-8 mode would accept a bad byte as a surrogate.
    A stream that cannot be reconfigured, such as a test's `StringIO`, is
    text already and is left alone.

    Args:
        stream: `sys.stdout`.
    """
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8", errors="strict", newline="\n")


def _utf8_lines(stream: TextIO) -> Iterable[str]:
    """Read a standard stream as UTF-8, one line decoded at a time.

    A text stream decodes in chunks, so a bad byte on line 40 surfaces
    while line 1 is being read, and the reader would name the wrong line.
    Reading the bytes and decoding each line on its own puts the failure on
    the line it belongs to. A stream with no byte layer, such as a test's
    `StringIO`, is text already and is read as it is.

    Args:
        stream: `sys.stdin`.

    Returns:
        The stream's lines as text.
    """
    buffer = getattr(stream, "buffer", None)
    if buffer is None:
        return stream
    return (line.decode("utf-8") for line in buffer)


def _discard_exit_flush() -> None:
    """Stop the interpreter reporting a closed pipe a second time at exit.

    The interpreter flushes stdout again when it exits. Pointing descriptor
    1 at nothing makes that flush succeed. A stdout with no descriptor, as
    under a test harness, has nothing to flush and is left alone, and the
    command's clean exit stands.
    """
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        os.close(devnull)
    except (OSError, ValueError, AttributeError):
        # No descriptor to redirect, so there is no exit flush to silence.
        # A harness stdout raises here, and the command has already
        # finished cleanly.
        return


def _import(_: argparse.Namespace) -> int:
    """Rebuild every catalogue the standard input carries, and print the census.

    Reads one line at a time and writes no file. The census is printed in
    the order the catalogue records arrived, one line per catalogue, so the
    numbers can be read beside what `parse` printed.

    A stream with no catalogue in it is refused. Without `pipefail`, a
    pipeline returns the last command's status, so a validator that passed
    an empty stream would hide the failed export in front of it.

    Args:
        _: Parsed arguments. `--check` is mandatory, so it carries nothing.

    Returns:
        Zero. A stream the reader rejects raises instead.

    The stream is read as UTF-8 whatever the locale says, one line decoded
    at a time, so a byte that is not UTF-8 is reported with its line and
    its offset inside that line.

    Raises:
        InterchangeEmpty: If the stream carries no catalogue, or standard
            input is closed.
    """
    if sys.stdin is None:
        msg = "standard input is closed"
        raise InterchangeEmpty(msg)
    catalogues = catalogue_interchange().decode(_utf8_lines(sys.stdin))
    if not catalogues:
        msg = "interchange carries no catalogues"
        raise InterchangeEmpty(msg)
    for catalogue in catalogues:
        print(
            f"{catalogue.source_id:<14}  {len(catalogue.preparations)} sauces, "
            f"{catalogue.resolved} derived, {catalogue.unresolved} unresolved"
        )
    read = sum(len(c.preparations) for c in catalogues)
    print(
        f"{len(catalogues)} catalogues and {read} preparations rebuilt. Nothing written."
    )
    return 0


def _diff(args: argparse.Namespace) -> int:
    """Compare two stored catalogues and print what caused each difference.

    The summary carries the tally, the blind spot, and what neither of them
    settles.

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
    _print_reach(report)
    print("  No row is adjudicated. An ocr-suspected row is a suspicion, and")
    print("  separating a scan artefact from a revision needs both lines read.")
    return 0


def _print_reach(report: Report) -> None:
    """Print how much of each witness the reader could see.

    The blind spot sits beside the counts rather than in a note, because a
    reader who sees how many rows the diff found has to see how much of the
    source it could not read. ADR-0014 records why.

    Args:
        report: The comparison being printed.
    """
    older, newer = report.entries_read
    if older is None or newer is None:
        print("  entries read  not recorded, so the blind spot is unknown")
        return
    print(
        f"  entries read  {older} of {report.older}, {newer} of {report.newer}, "
        f"a blind spot of {report.blind_spot}"
    )
    if report.scanned:
        print("  A witness is ocr. An unmatched row says the diff found no")
        print("  counterpart, never that the printing lacks one.")


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

    The heading names the root, and the root's own parent when it has one.
    `tree espagnole` says `derives from brown-roux`, because Escoffier opens
    Espagnole with brown roux and the tree beneath it is not the whole chain.

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
    # drawn from a near match cannot pass itself off as the root. A root
    # that states its own parent says so, because a mother is not a root.
    heading = f"{found.title if found else args.concept}  [{root}]"
    if found is not None and found.parent is not None:
        heading += f"  derives from {found.parent}"
    print(heading)
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

    Beside an unresolved parent the command prints the candidates the
    opening paragraph states, so a reader sees why the resolver refused. `CARDINAL
    SAUCE` states Béchamel and lobster butter, and the line says so.

    Below the parent it prints the recorded procedure, one operation per
    line, or says the preparation is unrecorded. The procedure is checked
    against the body before the first line is printed, so a misquoted
    record leaves stdout empty.

    Args:
        args: Parsed arguments carrying the concept to show and the source.

    Returns:
        Zero, or `NOT_FOUND` when nothing answers to the concept.

    Raises:
        ProcedureUnstated: If the recorded procedure misquotes the body.
    """
    concept = to_concept_id(args.concept)
    catalogue = catalogue_store().load(args.source or default_source_id())
    matches = catalogue.matches(concept)
    if not matches:
        print(f"no preparation named {args.concept!r}", file=sys.stderr)
        return NOT_FOUND

    preparation = matches[0]
    recorded = recorded_procedures()
    procedure = procedure_of(preparation, recorded)
    ref = preparation.ref
    print(preparation.title)
    print(
        f"entry {ref.entry}, line {ref.line}, {ref.fidelity.value} of {ref.source_id}"
    )
    for term in preparation.terms:
        print(f"  term  {term.surface}  [{term.language.value}]  {term.concept}")
    if preparation.parent is None:
        print("  parent  (unresolved)")
        print(f"  stated  {_stated(catalogue, preparation)}")
    else:
        print(f"  parent  {preparation.parent}")
    _print_procedure(procedure, recorded.recorder)
    print()
    print(_prose(preparation.body, args.chars))
    if len(matches) > 1:
        others = ", ".join(p.title for p in matches[1:])
        print(f"\nAlso matching {args.concept!r}: {others}", file=sys.stderr)
    return 0


def _stated(catalogue: Catalogue, preparation: Preparation) -> str:
    """Name the candidates an unresolved preparation states.

    Args:
        catalogue: The catalogue the preparation was read from.
        preparation: The preparation whose parent is unresolved.

    Returns:
        The stated candidates in the order the paragraph states them, or
        `no candidate` when the opening paragraph states none.
    """
    stated = stated_candidates(
        preparation.body, own_names(preparation), parent_candidates(catalogue)
    )
    return ", ".join(stated) if stated else "no candidate"


def _print_procedure(procedure: Procedure | None, recorder: str) -> None:
    """Print a checked procedure, or say the preparation is unrecorded.

    The heading line says how many operations and who recorded them. Each
    operation then takes one line: its verb, then what the clause states,
    in the order stated. A parameter whose words give no number says
    `(unresolved)`, because the slot is the one a parent uses.

    Args:
        procedure: The procedure the body was checked against, or `None`
            when the preparation is unrecorded.
        recorder: Who recorded it.
    """
    if procedure is None:
        print("  procedure  (unrecorded)")
        return
    count = len(procedure.operations)
    print(f"  procedure  {count} operations, recorded by {recorder}")
    for line in _operation_lines(procedure):
        print(line)


def _operation_lines(procedure: Procedure) -> list[str]:
    """Render every operation of a procedure, verbs aligned.

    Args:
        procedure: The procedure to render.

    Returns:
        One line per operation, in procedure order.
    """
    width = max(len(operation.verb.surface) for operation in procedure.operations)
    return [
        f"    {operation.verb.surface:<{width}}  {', '.join(_parts(operation))}".rstrip()
        for operation in procedure.operations
    ]


def _parts(operation: Operation) -> list[str]:
    """Render what one clause states, in the order the record holds it.

    Args:
        operation: The operation to render.

    Returns:
        Inputs first, then the instrument, the criterion, the duration,
        and every constraint, each as text.
    """
    parts = [_input(found) for found in operation.inputs]
    if operation.instrument is not None:
        parts.append(f"instrument: {operation.instrument.surface}")
    if operation.criterion is not None:
        parts.append(f"criterion: {_parameter(operation.criterion)}")
    if operation.duration is not None:
        parts.append(f"duration: {_parameter(operation.duration)}")
    parts.extend(operation.constraints)
    return parts


def _input(found: Input) -> str:
    """Render one input as its term, its language, and its quantity.

    Args:
        found: The input to render.

    Returns:
        The surface form, the language tag, and the quantity when one is
        stated.
    """
    text = f"{found.term.surface} [{found.term.language.value}]"
    if found.quantity is None:
        return text
    return f"{text} {_parameter(found.quantity)}"


def _parameter(parameter: Parameter) -> str:
    """Render a parameter as its number and unit, or its words and a marker.

    Args:
        parameter: The parameter to render.

    Returns:
        `1/4 pint` when the words give a number, and the words followed by
        `(unresolved)` when they do not.
    """
    if parameter.number is None:
        return f"{parameter.wording} (unresolved)"
    if parameter.unit is None:
        return str(parameter.number)
    return f"{parameter.number} {parameter.unit}"


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
    reads the first committed witness unless `--source` names another. The
    import command requires `--check`, so the verb cannot pass for a write.

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

    export = sub.add_parser(
        "export", help="write every stored catalogue to stdout as jsonl"
    )
    export.set_defaults(run=_export)

    imp = sub.add_parser("import", help="rebuild catalogues from jsonl on stdin")
    imp.add_argument(
        "--check",
        action="store_true",
        required=True,
        help="rebuild in memory and print the census. Mandatory: nothing is written",
    )
    imp.set_defaults(run=_import)
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

    Every command prints to standard output, so a reader that closes the
    pipe early is handled here once rather than in each command.

    Returns:
        Zero on success, `NOT_FOUND` when a lookup misses, `FAILED` when a
        source or store could not be read or written.
    """
    args = build_parser().parse_args(argv)
    try:
        code = int(args.run(args))
        sys.stdout.flush()
    except SaucierError as exc:
        print(f"saucier: {exc}", file=sys.stderr)
        return FAILED
    except BrokenPipeError:
        # A reader that closed the pipe early, as `head` does, has what it
        # asked for. The rest goes nowhere and the command exits clean.
        _discard_exit_flush()
        return 0
    return code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
