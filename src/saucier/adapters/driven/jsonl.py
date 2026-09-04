"""Carry catalogues as JSON Lines, one record per line.

The interchange, as ADR-0016 decides it. A stream holds catalogue records
and preparation records, and every record carries an envelope of `schema`,
`type`, and `id`. A program with none of these classes can read one line
and know what it holds and which catalogue it belongs to.

A catalogue record's id is the catalogue's source id, which names an
edition of a work. It carries the witness fields the domain needs, and that
does not make it a witness id. Two texts of one edition would share it, so
a stream carries at most one catalogue per source id. The identity that a
second text of one edition needs is later work.

The writer is deterministic. Catalogue records come first, in the order
given, then each catalogue's preparations in source order. Keys are emitted
in one fixed order, with no whitespace and no ASCII escaping, and every
line ends in one newline. Identical catalogues produce identical bytes.

The reader is strict. It consumes one line at a time and rejects, with the
line number, anything the schema does not describe. It accepts records in
any order. The schema's constants and the reader itself live in
`jsonl_records`, so that validation and rendering stay legible on their
own. This module holds the writer and the class that satisfies the port.

Examples:
    Write a stream and rebuild the catalogues from it:

    ```python
    import io

    from saucier.adapters.driven.jsonl import JsonlInterchange

    interchange = JsonlInterchange()
    stream = io.StringIO()
    stream.writelines(interchange.encode(catalogues))
    stream.seek(0)
    assert interchange.decode(stream) == tuple(catalogues)
    ```

See Also:
    - [saucier.ports.interchange][]: The contract this satisfies.
    - [saucier.adapters.driven.jsonl_records][]: The schema and the reader.
    - [saucier.adapters.driven.json_store][]: The working store, which this
      does not replace.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from typing import Any

from saucier.adapters.driven.jsonl_records import (
    CATALOGUE,
    PREPARATION,
    SCHEMA,
    Reader,
    preparation_id,
)
from saucier.domain.errors import CatalogueUnwritable, RecordRejected
from saucier.domain.models import Catalogue, Preparation

__all__ = ["CATALOGUE", "PREPARATION", "SCHEMA", "JsonlInterchange", "preparation_id"]


class JsonlInterchange:
    """The JSON Lines interchange, satisfying `CatalogueInterchange`.

    Examples:
        Encode to lines and decode them back:

        ```python
        interchange = JsonlInterchange()
        lines = list(interchange.encode([catalogue]))
        assert interchange.decode(lines) == (catalogue,)
        ```
    """

    def encode(self, catalogues: Iterable[Catalogue]) -> Iterator[str]:
        """Render catalogues as lines, catalogue records first.

        The catalogues are held before the first line is yielded, so a
        catalogue that cannot be read raises before any output exists. So
        does a catalogue with two preparations on one heading line, whose
        ids would collide and whose stream the reader would then refuse.

        Args:
            catalogues: The catalogues to carry, in the order to write them.

        Yields:
            One record per line, each ending in a newline.

        Raises:
            CatalogueUnwritable: If two preparations of one catalogue sit on
                one heading line.
        """
        held = tuple(catalogues)
        for catalogue in held:
            _check_lines(catalogue)
        for catalogue in held:
            yield _render(_catalogue_record(catalogue))
        for catalogue in held:
            for preparation in catalogue.preparations:
                yield _render(_preparation_record(catalogue.source_id, preparation))

    def decode(self, lines: Iterable[str]) -> tuple[Catalogue, ...]:
        """Rebuild every catalogue the lines carry.

        Args:
            lines: Lines of the interchange, in any order, one line per
                element. Blank lines are skipped, and line numbers in errors
                count them. The `Reader` in `jsonl_records` does the
                work. Decode each line on its own for an exact line
                on a UTF-8 failure, because a text stream decodes in chunks.

        Returns:
            The rebuilt catalogues, in the order their catalogue records
            appeared.

        Raises:
            RecordRejected: If any line is not a record this reader accepts,
                a line is not UTF-8, a preparation names a catalogue the
                stream never carries, a catalogue receives fewer preparations
                than it states, or a rebuilt catalogue violates a domain
                invariant.
        """
        reader = Reader()
        number = 0
        try:
            for number, line in enumerate(lines, 1):
                if line.strip():
                    reader.take(number, line)
        except UnicodeDecodeError as exc:
            # The iterator raises before the line exists, so the failing
            # line is the one after the last one read. That is exact when
            # each line is decoded on its own, as the command line does.
            msg = (
                f"line {number + 1}: not UTF-8 "
                f"({exc.reason} at byte {exc.start} of the line)"
            )
            raise RecordRejected(msg) from exc
        return reader.assemble()


def _check_lines(catalogue: Catalogue) -> None:
    """Refuse a catalogue whose preparation ids would collide.

    The domain identifies a preparation by its heading line but does not
    enforce that two never share one. The writer does, because a stream it
    wrote must be one its reader accepts.

    Args:
        catalogue: The catalogue about to be rendered.

    Raises:
        CatalogueUnwritable: If two preparations sit on one heading line.
    """
    seen: dict[int, str] = {}
    for preparation in catalogue.preparations:
        line = preparation.ref.line
        if line in seen:
            msg = (
                f"{catalogue.source_id} holds {seen[line]} and {preparation.title} "
                f"at line {line}, so their ids would collide"
            )
            raise CatalogueUnwritable(msg)
        seen[line] = preparation.title


def _render(record: dict[str, Any]) -> str:
    """Serialize one record as one line.

    Args:
        record: The record, with keys already in the order to emit.

    Returns:
        Compact JSON with no ASCII escaping, ending in a newline.
    """
    return json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"


def _catalogue_record(catalogue: Catalogue) -> dict[str, Any]:
    """Render a catalogue, apart from its preparations, as a catalogue record.

    The record states how many preparations follow it. A reader that
    receives fewer knows the stream was cut, and a catalogue with none says
    so in its own record.

    Args:
        catalogue: The catalogue whose witness, mothers, and count to carry.

    Returns:
        The record, keys in emission order.
    """
    witness, edition = catalogue.witness, catalogue.witness.edition
    return {
        "schema": SCHEMA,
        "type": CATALOGUE,
        "id": catalogue.source_id,
        "work": witness.work,
        "edition": {
            "statement": edition.statement,
            "stated_year": edition.stated_year,
            "impression": edition.impression,
            "copyright_year": edition.copyright_year,
        },
        "origin": witness.origin,
        "fidelity": witness.fidelity.value,
        "mothers": sorted(catalogue.mothers),
        "preparations": len(catalogue.preparations),
        "entries_read": catalogue.entries_read,
    }


def _preparation_record(source_id: str, preparation: Preparation) -> dict[str, Any]:
    """Render one preparation as a record naming its catalogue.

    The body comes last, so a reader skimming the head of a line sees the
    envelope, the names, and the parent before the prose.

    Args:
        source_id: The catalogue the preparation belongs to.
        preparation: The preparation to carry.

    Returns:
        The record, keys in emission order.
    """
    ref = preparation.ref
    return {
        "schema": SCHEMA,
        "type": PREPARATION,
        "id": preparation_id(source_id, ref.line),
        "catalogue": source_id,
        "title": preparation.title,
        "terms": [
            {"surface": t.surface, "language": t.language.value, "concept": t.concept}
            for t in preparation.terms
        ],
        "concept": preparation.concept,
        "parent": preparation.parent,
        "ref": {"entry": ref.entry, "line": ref.line, "fidelity": ref.fidelity.value},
        "body": preparation.body,
    }
