"""Carry catalogues as JSON Lines, one record per line.

The interchange, as ADR-0016 decides it. A stream holds witness records and
preparation records, and every record carries an envelope of `schema`,
`type`, and `id`. A program with none of these classes can read one line
and know what it holds and which text supports it.

The writer is deterministic. Witness records come first, in the order
given, then each witness's preparations in source order. Keys are emitted
in one fixed order, with no whitespace and no ASCII escaping, and every
line ends in one newline. Identical catalogues produce identical bytes.

The reader is strict. It consumes one line at a time and rejects, with the
line number, anything the schema does not describe: malformed JSON, an
unknown schema or type, a duplicate id, a field it does not name, a value
of the wrong type, a derived field that disagrees with its source, and a
preparation whose witness the stream never carries. It accepts records in
any order, so two exports joined with `cat` still rebuild. A `null` parent
is unresolved, and a blank one is damage.

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
    - [saucier.adapters.driven.json_store][]: The working store, which this
      does not replace.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import replace
from typing import Any

from saucier.domain.errors import EditionUnstated, RecordRejected
from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
from saucier.domain.types import ConceptId, Language, to_concept_id
from saucier.domain.witness import Edition, Fidelity, Witness

SCHEMA = "saucier/1"
"""The version of the interchange this module writes and reads."""

WITNESS = "witness"
"""Record type carrying what rebuilds a catalogue's frame."""

PREPARATION = "preparation"
"""Record type carrying one preparation and the witness it cites."""

_ENVELOPE = ("schema", "type", "id")
_WITNESS_KEYS = frozenset(
    (*_ENVELOPE, "work", "edition", "origin", "fidelity", "mothers", "entries_read")
)
_EDITION_KEYS = frozenset(("statement", "stated_year", "impression", "copyright_year"))
_PREPARATION_KEYS = frozenset(
    (*_ENVELOPE, "witness", "title", "terms", "concept", "parent", "ref", "body")
)
_TERM_KEYS = frozenset(("surface", "language", "concept"))
_REF_KEYS = frozenset(("entry", "line", "fidelity"))
_DAMAGE = (KeyError, TypeError, ValueError, EditionUnstated)
"""What a damaged record raises while it is rebuilt. Reported, never raised raw."""


def preparation_id(source_id: str, line: int) -> str:
    """Address one preparation inside one witness.

    The heading line identifies a preparation where an entry number may
    not, because a scan repeats numbers. The id says where a reader can
    check the claim. It makes no claim that two witnesses hold one sauce.

    Args:
        source_id: The witness the preparation was read from.
        line: The line its heading sits on.

    Returns:
        The witness and the line, joined.
    """
    return f"{source_id}:line:{line}"


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
        """Render catalogues as lines, witnesses first.

        The catalogues are held before the first line is yielded, so a
        catalogue that cannot be read raises before any output exists.

        Args:
            catalogues: The catalogues to carry, in the order to write them.

        Yields:
            One record per line, each ending in a newline.
        """
        held = tuple(catalogues)
        for catalogue in held:
            yield _render(_witness_record(catalogue))
        for catalogue in held:
            for preparation in catalogue.preparations:
                yield _render(_preparation_record(catalogue.source_id, preparation))

    def decode(self, lines: Iterable[str]) -> tuple[Catalogue, ...]:
        """Rebuild every catalogue the lines carry.

        Args:
            lines: Lines of the interchange, in any order. Blank lines are
                skipped, and line numbers in errors count them.

        Returns:
            The rebuilt catalogues, in the order their witness records appeared.

        Raises:
            RecordRejected: If any line is not a record this reader accepts,
                a preparation names a witness the stream never carries, or
                a rebuilt catalogue violates a domain invariant.
        """
        reader = _Reader()
        for number, line in enumerate(lines, 1):
            if line.strip():
                reader.take(number, line)
        return reader.assemble()


class _Reader:
    """What the reader holds between the first line and the last.

    Attributes:
        frames (dict[str, Catalogue]): Witness records rebuilt so far, keyed
            by source id, each an empty catalogue awaiting its preparations.
        preparations (dict[str, list[Preparation]]): Preparations read so
            far, grouped by the witness they name.
        seen (dict[str, int]): Every id read so far and the line it was on.
        cited (dict[str, int]): Each witness a preparation names and the
            first line that named it, for reporting a dangling reference.

    Examples:
        Feed lines one at a time and assemble at the end:

        ```python
        reader = _Reader()
        for number, line in enumerate(lines, 1):
            reader.take(number, line)
        catalogues = reader.assemble()
        ```
    """

    def __init__(self) -> None:
        """Start with nothing read."""
        self.frames: dict[str, Catalogue] = {}
        self.preparations: dict[str, list[Preparation]] = {}
        self.seen: dict[str, int] = {}
        self.cited: dict[str, int] = {}

    def take(self, number: int, line: str) -> None:
        """Read one line, and reject it with its number if it is not a record.

        Args:
            number: The line's position in the stream, from 1.
            line: The text of the line.

        Raises:
            RecordRejected: If the line is not a record this reader accepts.
        """
        try:
            record = _parse(line)
            kind, identity = _envelope(record)
            if identity in self.seen:
                msg = f"duplicate id {identity!r}, first seen at line {self.seen[identity]}"
                raise ValueError(msg)
            self.seen[identity] = number
            if kind == WITNESS:
                self.frames[identity] = _frame_from(record)
            else:
                witness, preparation = _preparation_from(record)
                self.cited.setdefault(witness, number)
                self.preparations.setdefault(witness, []).append(preparation)
        except json.JSONDecodeError as exc:
            msg = f"line {number}: not JSON ({exc.msg} at column {exc.colno})"
            raise RecordRejected(msg) from exc
        except _DAMAGE as exc:
            raise RecordRejected(f"line {number}: {_describe(exc)}") from exc

    def assemble(self) -> tuple[Catalogue, ...]:
        """Build every catalogue once the stream has ended.

        Preparations are ordered by their heading line, which is source
        order, so a shuffled stream rebuilds the same catalogue.

        Returns:
            The catalogues, in the order their witness records appeared.

        Raises:
            RecordRejected: If a preparation names a witness the stream never
                carried, or a catalogue refuses its preparations.
        """
        for witness, number in self.cited.items():
            if witness not in self.frames:
                msg = (
                    f"line {number}: preparation names witness {witness!r}, "
                    "which the stream does not carry"
                )
                raise RecordRejected(msg)
        built = []
        for source_id, frame in self.frames.items():
            ordered = sorted(self.preparations.get(source_id, ()), key=_line_of)
            try:
                built.append(replace(frame, preparations=tuple(ordered)))
            except ValueError as exc:
                raise RecordRejected(f"witness {source_id!r}: {exc}") from exc
        return tuple(built)


def _line_of(preparation: Preparation) -> int:
    """Read the heading line a preparation sits on, for ordering.

    Args:
        preparation: The preparation to order.

    Returns:
        Its heading line.
    """
    return preparation.ref.line


def _describe(exc: BaseException) -> str:
    """Word a rebuild failure for the line it happened on.

    A `KeyError` carries only the key, so it is spelled out. Every other
    failure already says what was wrong.

    Args:
        exc: What the rebuild raised.

    Returns:
        A sentence fragment naming the fault.
    """
    if isinstance(exc, KeyError):
        return f"no {exc.args[0]!r} field"
    return str(exc)


def _render(record: dict[str, Any]) -> str:
    """Serialize one record as one line.

    Args:
        record: The record, with keys already in the order to emit.

    Returns:
        Compact JSON with no ASCII escaping, ending in a newline.
    """
    return json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"


def _witness_record(catalogue: Catalogue) -> dict[str, Any]:
    """Render a catalogue's frame as a witness record.

    Args:
        catalogue: The catalogue whose witness, mothers, and count to carry.

    Returns:
        The record, keys in emission order.
    """
    witness, edition = catalogue.witness, catalogue.witness.edition
    return {
        "schema": SCHEMA,
        "type": WITNESS,
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
        "entries_read": catalogue.entries_read,
    }


def _preparation_record(source_id: str, preparation: Preparation) -> dict[str, Any]:
    """Render one preparation as a record naming its witness.

    The body comes last, so a reader skimming the head of a line sees the
    envelope, the names, and the parent before the prose.

    Args:
        source_id: The witness the preparation was read from.
        preparation: The preparation to carry.

    Returns:
        The record, keys in emission order.
    """
    ref = preparation.ref
    return {
        "schema": SCHEMA,
        "type": PREPARATION,
        "id": preparation_id(source_id, ref.line),
        "witness": source_id,
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


def _parse(line: str) -> dict[str, Any]:
    """Read one line as one JSON object.

    Args:
        line: The text of the line.

    Returns:
        The object the line holds.

    Raises:
        json.JSONDecodeError: If the line is not JSON.
        TypeError: If the line is JSON but not an object.
    """
    record = json.loads(line)
    if not isinstance(record, dict):
        msg = f"a record is a JSON object, not {type(record).__name__}"
        raise TypeError(msg)
    return record


def _envelope(record: dict[str, Any]) -> tuple[str, str]:
    """Check the three fields every record carries.

    Args:
        record: The parsed record.

    Returns:
        The record type and the id.

    Raises:
        ValueError: If the schema is not the one this reader accepts, the
            type is not one it knows, or the id is missing or blank.
    """
    schema = record.get("schema")
    if schema != SCHEMA:
        msg = f"unknown schema {schema!r}, this reader accepts {SCHEMA!r}"
        raise ValueError(msg)
    kind = record.get("type")
    if kind not in (WITNESS, PREPARATION):
        msg = f"unknown record type {kind!r}"
        raise ValueError(msg)
    identity = record.get("id")
    if not isinstance(identity, str) or not identity.strip():
        msg = "a record needs an id"
        raise ValueError(msg)
    return kind, identity


def _frame_from(record: dict[str, Any]) -> Catalogue:
    """Rebuild a catalogue's frame from a witness record.

    The source id is recomputed from the work and the edition, so a record
    whose id names another text is rejected rather than answered to.

    Args:
        record: A witness record whose envelope has been checked.

    Returns:
        A catalogue with its witness, mothers, and count, and no preparations.

    Raises:
        ValueError: If a field is absent, unexpected, or of the wrong type,
            or the id disagrees with the witness it describes.
    """
    fields = _fields(record, _WITNESS_KEYS, "witness record")
    edition = _fields(fields["edition"], _EDITION_KEYS, "edition")
    witness = Witness(
        work=_text(fields["work"]),
        origin=_text(fields["origin"]),
        fidelity=Fidelity(_text(fields["fidelity"])),
        edition=Edition(
            statement=_text_or_none(edition["statement"]),
            stated_year=_int_or_none(edition["stated_year"]),
            impression=_text_or_none(edition["impression"]),
            copyright_year=_int_or_none(edition["copyright_year"]),
        ),
    )
    if witness.source_id != fields["id"]:
        msg = f"witness record {fields['id']!r} describes {witness.source_id!r}"
        raise ValueError(msg)
    return Catalogue(
        witness=witness,
        mothers=_concepts(fields["mothers"]),
        entries_read=_int_or_none(fields["entries_read"]),
    )


def _preparation_from(record: dict[str, Any]) -> tuple[str, Preparation]:
    """Rebuild one preparation from its record.

    The concept and the id both derive from other fields, so both are
    recomputed and compared. A `null` parent is unresolved. Anything else
    has to be a concept id, so a blank is damage.

    Args:
        record: A preparation record whose envelope has been checked.

    Returns:
        The witness the record names, and the preparation.

    Raises:
        ValueError: If a field is absent, unexpected, or of the wrong type,
            or a derived field disagrees with what it derives from.
    """
    fields = _fields(record, _PREPARATION_KEYS, "preparation record")
    witness = _text(fields["witness"])
    ref = _fields(fields["ref"], _REF_KEYS, "ref")
    parent = fields["parent"]
    preparation = Preparation(
        title=_text(fields["title"]),
        terms=tuple(_term_from(t) for t in _list(fields["terms"], "terms")),
        body=_text(fields["body"]),
        ref=SourceRef(
            source_id=witness,
            entry=_int(ref["entry"]),
            line=_int(ref["line"]),
            fidelity=Fidelity(_text(ref["fidelity"])),
        ),
        parent=None if parent is None else _concept(parent),
    )
    if fields["concept"] != preparation.concept:
        msg = f"concept {fields['concept']!r} is not folded from the terms"
        raise ValueError(msg)
    wanted = preparation_id(witness, preparation.ref.line)
    if fields["id"] != wanted:
        msg = f"id {fields['id']!r} does not address {wanted!r}"
        raise ValueError(msg)
    return witness, preparation


def _term_from(payload: Any) -> Term:
    """Rebuild one term, checking the concept written beside it.

    Args:
        payload: One element of a record's `terms`.

    Returns:
        The term.

    Raises:
        ValueError: If a field is absent, unexpected, or of the wrong type,
            or the written concept is not folded from the surface.
    """
    fields = _fields(payload, _TERM_KEYS, "term")
    term = Term(
        surface=_text(fields["surface"]), language=Language(_text(fields["language"]))
    )
    if fields["concept"] != term.concept:
        msg = f"concept {fields['concept']!r} is not folded from {term.surface!r}"
        raise ValueError(msg)
    return term


def _fields(payload: Any, expected: frozenset[str], what: str) -> dict[str, Any]:
    """Check that an object carries exactly the fields the schema names.

    Args:
        payload: The value that should be an object.
        expected: The field names the schema gives it.
        what: What the object is, for the message.

    Returns:
        The object, unchanged.

    Raises:
        TypeError: If the value is not an object.
        ValueError: If a field is absent or unexpected.
    """
    if not isinstance(payload, dict):
        msg = f"{what} is not a JSON object"
        raise TypeError(msg)
    if set(payload) != expected:
        absent = sorted(expected - set(payload))
        extra = sorted(set(payload) - expected)
        msg = f"{what} fields: absent {absent}, unexpected {extra}"
        raise ValueError(msg)
    return payload


def _list(payload: Any, what: str) -> list[Any]:
    """Check that a value is a JSON array.

    Args:
        payload: The value that should be an array.
        what: What the array is, for the message.

    Returns:
        The array, unchanged.

    Raises:
        TypeError: If the value is not an array.
    """
    if not isinstance(payload, list):
        msg = f"{what} is not a JSON array"
        raise TypeError(msg)
    return payload


def _text(value: Any) -> str:
    """Read a required string field.

    Args:
        value: The stored value.

    Returns:
        The string.

    Raises:
        TypeError: If the value is not a string.
    """
    if not isinstance(value, str):
        msg = f"expected a string, not {value!r}"
        raise TypeError(msg)
    return value


def _text_or_none(value: Any) -> str | None:
    """Read an optional string field, keeping `null` distinct from empty.

    Args:
        value: The stored value.

    Returns:
        The string, or None when the record stored `null`.
    """
    return None if value is None else _text(value)


def _int(value: Any) -> int:
    """Read a required whole-number field.

    A JSON `true` is not a count, so booleans are refused although Python
    would accept one as an integer.

    Args:
        value: The stored value.

    Returns:
        The number.

    Raises:
        TypeError: If the value is not a whole number.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"expected a whole number, not {value!r}"
        raise TypeError(msg)
    return value


def _int_or_none(value: Any) -> int | None:
    """Read an optional whole number, keeping `null` distinct from zero.

    Args:
        value: The stored value.

    Returns:
        The number, or None when the record stored `null`.
    """
    return None if value is None else _int(value)


def _concept(value: Any) -> ConceptId:
    """Read a concept id, refusing one that is not its own fold.

    A parent or a mother is written folded. A value that folds to something
    else was never a concept id, and reading it as one would let a stream
    name a parent the catalogue cannot find.

    Args:
        value: The stored value.

    Returns:
        The concept id.

    Raises:
        ValueError: If the value is not a string equal to its own fold.
    """
    text = _text(value)
    if to_concept_id(text) != text:
        msg = f"{text!r} is not a concept id"
        raise ValueError(msg)
    return ConceptId(text)


def _concepts(payload: Any) -> frozenset[ConceptId]:
    """Read a list of concept ids with no repeats.

    Args:
        payload: The stored value.

    Returns:
        The concepts as a set.

    Raises:
        ValueError: If a concept repeats. A set would drop the repeat
            silently, and a stream that repeats a mother is damaged.
    """
    concepts = [_concept(c) for c in _list(payload, "mothers")]
    if len(set(concepts)) != len(concepts):
        msg = "mothers repeat a concept"
        raise ValueError(msg)
    return frozenset(concepts)
