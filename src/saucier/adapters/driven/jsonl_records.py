"""The record schema of the interchange, and the reader that enforces it.

The constants here name what `saucier/1` allows: the two record types and
the exact field set of every object. The reader consumes one line at a
time and rejects, with the line number, anything outside that set. It is
split from the writer in `jsonl` so that validation and rendering stay
legible on their own.

Every field the schema names is checked to be present before it is read,
so a damaged record is always reported by what is wrong with it and never
by a bare key. An object that repeats a key is rejected, because `json`
would keep the last value and say nothing. A catalogue record states how
many preparations follow it, so a stream cut at a line boundary is
rejected rather than rebuilt short. A byte that is not UTF-8 is rejected
with its line. A `null` parent is unresolved, and a blank one is damage.

Examples:
    Feed lines one at a time and assemble at the end:

    ```python
    from saucier.adapters.driven.jsonl_records import Reader

    reader = Reader()
    for number, line in enumerate(lines, 1):
        if line.strip():
            reader.take(number, line)
    catalogues = reader.assemble()
    ```

See Also:
    - [saucier.adapters.driven.jsonl][]: The interchange that writes these
      records and drives this reader.
    - [saucier.ports.interchange][]: The contract both satisfy together.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from saucier.domain.errors import EditionUnstated, RecordRejected
from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
from saucier.domain.types import ConceptId, Language, to_concept_id
from saucier.domain.witness import Edition, Fidelity, Witness

SCHEMA = "saucier/1"
"""The version of the interchange this module writes and reads."""

CATALOGUE = "catalogue"
"""Record type carrying a catalogue apart from its preparations."""

PREPARATION = "preparation"
"""Record type carrying one preparation and the catalogue it belongs to."""

_ENVELOPE = ("schema", "type", "id")
_CATALOGUE_KEYS = frozenset(
    (
        *_ENVELOPE,
        "work",
        "edition",
        "origin",
        "fidelity",
        "mothers",
        "preparations",
        "entries_read",
    )
)
_EDITION_KEYS = frozenset(("statement", "stated_year", "impression", "copyright_year"))
_PREPARATION_KEYS = frozenset(
    (*_ENVELOPE, "catalogue", "title", "terms", "concept", "parent", "ref", "body")
)
_TERM_KEYS = frozenset(("surface", "language", "concept"))
_REF_KEYS = frozenset(("entry", "line", "fidelity"))


class _WrongType(TypeError):
    """A field holds a value of a type the schema does not give it.

    A private subclass, so the reader catches the wrong types it found in
    the stream and never a `TypeError` raised by a bug in its own code.

    Examples:
        Raised by the field readers:

        ```python
        _int("2963")  # _WrongType: expected a whole number, not '2963'
        ```
    """


_DAMAGE = (_WrongType, ValueError, EditionUnstated)
"""What a damaged record raises while it is rebuilt. Reported, never raised raw.

A bare `TypeError` is not in the set. One raised inside the reader is a
bug in the reader, and it surfaces as a traceback rather than as damage
attributed to a line of the stream."""


def preparation_id(source_id: str, line: int) -> str:
    """Address one preparation inside one catalogue.

    The heading line identifies a preparation where an entry number may
    not, because a scan repeats numbers. The id says where a reader can
    check the claim. It makes no claim that two catalogues hold one sauce.

    Args:
        source_id: The catalogue the preparation belongs to, which is the
            source id of its witness.
        line: The line its heading sits on.

    Returns:
        The catalogue and the line, joined.
    """
    return f"{source_id}:line:{line}"


class Reader:
    """What the reader holds between the first line and the last.

    Attributes:
        catalogues (dict[str, Catalogue]): Catalogue records rebuilt so far,
            keyed by source id, each without its preparations yet.
        counts (dict[str, int]): How many preparations each catalogue record
            states, keyed by source id.
        preparations (dict[str, list[Preparation]]): Preparations read so
            far, grouped by the catalogue they name.
        seen (dict[str, int]): Every id read so far and the line it was on.
        cited (dict[str, int]): Each catalogue a preparation names and the
            first line that named it, for reporting a dangling reference.

    Examples:
        Feed lines one at a time and assemble at the end:

        ```python
        reader = Reader()
        for number, line in enumerate(lines, 1):
            reader.take(number, line)
        catalogues = reader.assemble()
        ```
    """

    def __init__(self) -> None:
        """Start with nothing read: no catalogues, counts, preparations, or ids."""
        self.catalogues: dict[str, Catalogue] = {}
        self.counts: dict[str, int] = {}
        self.preparations: dict[str, list[Preparation]] = {}
        self.seen: dict[str, int] = {}
        self.cited: dict[str, int] = {}

    def take(self, number: int, line: str) -> None:
        """Read one line, and reject it with its number if it is not a record.

        Malformed JSON is reported with the column the parser stopped at,
        counted from 1 along the line rather than from the last newline. A
        catalogue record is rebuilt without its preparations, and a
        preparation record is filed under the catalogue it names.
        Everything else the rebuild raises is reported in its own words.

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
            if kind == CATALOGUE:
                self.catalogues[identity], self.counts[identity] = _catalogue_from(
                    record
                )
            else:
                catalogue, preparation = _preparation_from(record)
                self.cited.setdefault(catalogue, number)
                self.preparations.setdefault(catalogue, []).append(preparation)
        except json.JSONDecodeError as exc:
            msg = f"line {number}: not JSON ({exc.msg} at column {exc.pos + 1})"
            raise RecordRejected(msg) from exc
        except RecursionError as exc:
            msg = f"line {number}: not JSON (nested too deep)"
            raise RecordRejected(msg) from exc
        except _DAMAGE as exc:
            raise RecordRejected(f"line {number}: {exc}") from exc

    def assemble(self) -> tuple[Catalogue, ...]:
        """Build every catalogue once the stream has ended.

        Preparations keep the order their records arrived in. The writer
        emits them in the catalogue's own order, so a stream read back as
        written rebuilds the catalogue exactly, whatever its order was.

        Returns:
            The catalogues, in the order their catalogue records appeared.

        Raises:
            RecordRejected: If a preparation names a catalogue the stream never
                carried, a catalogue receives fewer or more preparations than
                its record states, a preparation cites another fidelity than
                its catalogue, or a catalogue refuses its preparations.
        """
        for catalogue, number in self.cited.items():
            if catalogue not in self.catalogues:
                msg = (
                    f"line {number}: preparation names catalogue {catalogue!r}, "
                    "which the stream does not carry"
                )
                raise RecordRejected(msg)
        built = []
        for source_id, catalogue in self.catalogues.items():
            carried = self.preparations.get(source_id, [])
            self._check_count(source_id, len(carried))
            self._check_fidelity(source_id, catalogue, carried)
            try:
                built.append(replace(catalogue, preparations=tuple(carried)))
            except ValueError as exc:
                raise RecordRejected(f"catalogue {source_id!r}: {exc}") from exc
        return tuple(built)

    def _check_count(self, source_id: str, carried: int) -> None:
        """Refuse a catalogue that received a different number than it states.

        A stream cut at a line boundary is otherwise complete JSON, so the
        count is the only evidence of the cut.

        Args:
            source_id: The catalogue being assembled.
            carried: How many preparations the stream carried for it.

        Raises:
            RecordRejected: If the count disagrees, naming the catalogue
                record's line.
        """
        stated = self.counts[source_id]
        if carried != stated:
            msg = (
                f"line {self.seen[source_id]}: catalogue {source_id!r} states "
                f"{stated} preparations, the stream carries {carried}"
            )
            raise RecordRejected(msg)

    def _check_fidelity(
        self, source_id: str, catalogue: Catalogue, carried: list[Preparation]
    ) -> None:
        """Refuse a preparation that cites another fidelity than its catalogue.

        The domain refuses this too, but at the catalogue, without a line.
        The reader knows the line and says it.

        Args:
            source_id: The catalogue being assembled.
            catalogue: The catalogue rebuilt so far, carrying the witness.
            carried: Its preparations.

        Raises:
            RecordRejected: If a preparation's fidelity disagrees, naming the
                preparation's line.
        """
        for preparation in carried:
            if preparation.ref.fidelity != catalogue.fidelity:
                line = self.seen[preparation_id(source_id, preparation.ref.line)]
                msg = (
                    f"line {line}: {preparation.title} cites {source_id} at "
                    f"{preparation.ref.fidelity}, in a catalogue at {catalogue.fidelity}"
                )
                raise RecordRejected(msg)


def _parse(line: str) -> dict[str, Any]:
    """Read one line as one JSON object.

    Args:
        line: The text of the line.

    Returns:
        The object the line holds.

    Raises:
        json.JSONDecodeError: If the line is not JSON.
        _WrongType: If the line is JSON but not an object.
        ValueError: If an object repeats a key.
    """
    record = json.loads(line, object_pairs_hook=_object)
    if not isinstance(record, dict):
        msg = f"a record is a JSON object, not {type(record).__name__}"
        raise _WrongType(msg)
    return record


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build one JSON object, refusing a key that repeats.

    `json` keeps the last value of a repeated key and reports nothing, so
    a line carrying `parent` twice would rewrite a derivation silently.

    Args:
        pairs: The object's members in the order the line gives them.

    Returns:
        The object as a dictionary.

    Raises:
        ValueError: If a key appears more than once.
    """
    keys = [key for key, _ in pairs]
    if len(set(keys)) != len(keys):
        repeated = sorted({key for key in keys if keys.count(key) > 1})
        msg = f"object repeats a key: {repeated}"
        raise ValueError(msg)
    return dict(pairs)


def _envelope(record: dict[str, Any]) -> tuple[str, str]:
    """Check the three fields every record carries.

    The type is `catalogue` or `preparation`. A catalogue record's id is a
    source id, and a repeat of one is a duplicate, because version one
    carries one catalogue per source id.

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
    if kind not in (CATALOGUE, PREPARATION):
        msg = f"unknown record type {kind!r}"
        raise ValueError(msg)
    identity = record.get("id")
    if not isinstance(identity, str) or not identity.strip():
        msg = "a record needs an id"
        raise ValueError(msg)
    return kind, identity


def _catalogue_from(record: dict[str, Any]) -> tuple[Catalogue, int]:
    """Rebuild a catalogue, apart from its preparations, from its record.

    The source id is recomputed from the work and the edition, so a record
    whose id names another text is rejected rather than answered to.

    Args:
        record: A catalogue record whose envelope has been checked.

    Returns:
        A catalogue with its witness, mothers, and entry count, and no
        preparations, with the number of preparations the record states.

    Raises:
        ValueError: If a field is absent, unexpected, or of the wrong type,
            or the id disagrees with the witness it describes.
    """
    fields = _fields(record, _CATALOGUE_KEYS, "catalogue record")
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
        msg = f"catalogue record {fields['id']!r} describes {witness.source_id!r}"
        raise ValueError(msg)
    catalogue = Catalogue(
        witness=witness,
        mothers=_concepts(fields["mothers"]),
        entries_read=_int_or_none(fields["entries_read"]),
    )
    stated = _int(fields["preparations"])
    if stated < 0:
        msg = f"a catalogue cannot state {stated} preparations"
        raise ValueError(msg)
    return catalogue, stated


def _preparation_from(record: dict[str, Any]) -> tuple[str, Preparation]:
    """Rebuild one preparation from its record.

    The concept and the id both derive from other fields, so both are
    recomputed and compared. A `null` parent is unresolved. Anything else
    has to be a concept id, so a blank is damage.

    Args:
        record: A preparation record whose envelope has been checked.

    Returns:
        The catalogue the record names, and the preparation.

    Raises:
        ValueError: If a field is absent, unexpected, or of the wrong type,
            or a derived field disagrees with what it derives from.
    """
    fields = _fields(record, _PREPARATION_KEYS, "preparation record")
    catalogue = _text(fields["catalogue"])
    ref = _fields(fields["ref"], _REF_KEYS, "ref")
    parent = fields["parent"]
    preparation = Preparation(
        title=_text(fields["title"]),
        terms=tuple(_term_from(t) for t in _list(fields["terms"], "terms")),
        body=_text(fields["body"]),
        ref=SourceRef(
            source_id=catalogue,
            entry=_int(ref["entry"]),
            line=_int(ref["line"]),
            fidelity=Fidelity(_text(ref["fidelity"])),
        ),
        parent=None if parent is None else _concept(parent),
    )
    if fields["concept"] != preparation.concept:
        msg = f"concept {fields['concept']!r} is not folded from the terms"
        raise ValueError(msg)
    wanted = preparation_id(catalogue, preparation.ref.line)
    if fields["id"] != wanted:
        msg = f"id {fields['id']!r} does not address {wanted!r}"
        raise ValueError(msg)
    return catalogue, preparation


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
        _WrongType: If the value is not an object.
        ValueError: If a field is absent or unexpected.
    """
    if not isinstance(payload, dict):
        msg = f"{what} is not a JSON object"
        raise _WrongType(msg)
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
        _WrongType: If the value is not an array.
    """
    if not isinstance(payload, list):
        msg = f"{what} is not a JSON array"
        raise _WrongType(msg)
    return payload


def _text(value: Any) -> str:
    """Read a required string field.

    Args:
        value: The stored value.

    Returns:
        The string.

    Raises:
        _WrongType: If the value is not a string.
    """
    if not isinstance(value, str):
        msg = f"expected a string, not {value!r}"
        raise _WrongType(msg)
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
        _WrongType: If the value is not a whole number.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"expected a whole number, not {value!r}"
        raise _WrongType(msg)
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
    else was never a concept id. This checks the form only. Whether the
    concept names anything in the catalogue is not a domain invariant, and
    the reader does not add rules the domain does not hold.

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
