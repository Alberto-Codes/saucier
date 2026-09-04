"""Persist catalogues as JSON files.

JSON while a human still checks the parser's work by eye. ADR-0006
predicted it would fail when appending one record meant rewriting the file.
It did not, because each witness has a file of its own. What a snapshot
cannot do is leave the process. A program without these classes has to learn
the nested document before it can read one preparation. The interchange in
`jsonl` does that job, and this store keeps its own. ADR-0016 records the
split.

A stored file states what it is. The witness block carries the work, the
edition read from the front matter, the fidelity, and the origin, so a reader
opening one file learns which printing it holds. The id is recomputed from
that block on the way back in, so a file that has been renamed is reported
rather than answered with.

A write goes to a temporary file and is renamed over the target, so an
interrupted run leaves the previous catalogue intact. A damaged file is
reported as a domain error, because a derived file that will not parse is a
situation to report, not a bug in the reader.

Examples:
    Write a catalogue and read it back unchanged:

    ```python
    from pathlib import Path

    from saucier.adapters.driven.json_store import JsonCatalogueStore

    store = JsonCatalogueStore(Path("data"))
    store.save(catalogue)
    assert store.load(catalogue.source_id) == catalogue
    ```

See Also:
    - [saucier.ports.store][]: The contract this satisfies.
    - [saucier.adapters.driven.jsonl][]: The interchange, which carries a
      catalogue out of the process.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from saucier.domain.errors import (
    CatalogueUnwritable,
    EditionUnstated,
    SourceUnreadable,
)
from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
from saucier.domain.types import ConceptId, Language, to_concept_id
from saucier.domain.witness import Edition, Fidelity, Witness


@dataclass(frozen=True, slots=True)
class JsonCatalogueStore:
    """A directory of catalogue JSON files, one per source.

    Attributes:
        directory (Path): Where catalogue files are written.

    Examples:
        One file per source, named for it:

        ```python
        store = JsonCatalogueStore(Path("data"))
        store.save(catalogue)  # writes data/escoffier-1909.json
        ```
    """

    directory: Path

    def path_for(self, source_id: str) -> Path:
        """Resolve the file backing one source's catalogue.

        Args:
            source_id: Identifier of the source.

        Returns:
            Path to that source's catalogue file.

        Raises:
            CatalogueUnwritable: If the source id is not a plain file name,
                which would send the write outside the store.
        """
        if source_id != Path(source_id).name or source_id in {"", ".", ".."}:
            msg = f"source id is not a plain file name: {source_id!r}"
            raise CatalogueUnwritable(msg)
        return self.directory / f"{source_id}.json"

    def save(self, catalogue: Catalogue) -> str:
        """Write a catalogue, replacing any previous one for its source.

        The whole file is rendered every time, witness block and entry count
        included. One added record rewrites every other record. That is the
        cost of a snapshot, and ADR-0016 records that it is a cost rather
        than the break the next store waits for.

        Writes a temporary file and renames it over the target, so an
        interrupted run leaves the previous catalogue intact rather than a
        half-written one.

        Args:
            catalogue: The catalogue to persist.

        Returns:
            The path written.

        Raises:
            CatalogueUnwritable: If the directory or the file cannot be
                written.
        """
        path = self.path_for(catalogue.source_id)
        payload = {
            "witness": _witness_dict(catalogue.witness),
            "entries_read": catalogue.entries_read,
            "mothers": sorted(catalogue.mothers),
            "preparations": [_as_dict(p) for p in catalogue.preparations],
        }
        rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        temporary = path.with_suffix(".json.tmp")
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            temporary.write_text(rendered, encoding="utf-8")
            os.replace(temporary, path)
        except OSError as exc:
            msg = f"cannot write catalogue to {path}: {exc}"
            raise CatalogueUnwritable(msg) from exc
        return str(path)

    def load(self, source_id: str) -> Catalogue:
        """Read back a previously saved catalogue.

        A stored file that names no edition year, or an unknown fidelity, is
        damage rather than a catalogue. So is a file whose witness names a
        different source than the one asked for, because the id is recomputed
        from the witness rather than read from the file. An entry count of
        `null` is not damage. It means no count was recorded.

        Args:
            source_id: Identifier of the source whose catalogue to load.

        Returns:
            The stored catalogue, witness included.

        Raises:
            SourceUnreadable: If no catalogue is stored for that source, or
                the stored file is not readable, not JSON, or not shaped like
                a catalogue.
        """
        path = self.path_for(source_id)
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            msg = f"no catalogue stored for {source_id} at {path}. Run `saucier parse`"
            raise SourceUnreadable(msg) from exc
        except (OSError, UnicodeDecodeError) as exc:
            msg = f"cannot read catalogue at {path}: {exc}"
            raise SourceUnreadable(msg) from exc

        try:
            payload = json.loads(text)
            catalogue = Catalogue(
                witness=_witness_from_dict(payload["witness"]),
                preparations=tuple(_from_dict(p) for p in payload["preparations"]),
                mothers=frozenset(to_concept_id(m) for m in payload["mothers"]),
                entries_read=_int_or_none(payload["entries_read"]),
            )
        except (
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
            EditionUnstated,
        ) as exc:
            msg = (
                f"catalogue at {path} is damaged: {exc}. Run `saucier parse` to rebuild"
            )
            raise SourceUnreadable(msg) from exc

        if catalogue.source_id != source_id:
            # The id is recomputed from the witness rather than trusted, so a
            # file under the wrong name would otherwise answer to it.
            msg = (
                f"catalogue at {path} says it is {catalogue.source_id}, "
                f"not {source_id}. Run `saucier parse` to rebuild"
            )
            raise SourceUnreadable(msg)
        return catalogue


def _witness_dict(witness: Witness) -> dict[str, Any]:
    """Render a witness as JSON-safe primitives.

    `source_id` is written for a reader's convenience. It derives from the
    work and the edition year, so the loader recomputes it rather than
    trusting the file.

    Args:
        witness: The witness to render.

    Returns:
        A dictionary of JSON-safe values.
    """
    edition = witness.edition
    return {
        "source_id": witness.source_id,
        "work": witness.work,
        "origin": witness.origin,
        "fidelity": witness.fidelity.value,
        "edition": {
            "statement": edition.statement,
            "stated_year": edition.stated_year,
            "impression": edition.impression,
            "copyright_year": edition.copyright_year,
        },
    }


def _witness_from_dict(payload: dict[str, Any]) -> Witness:
    """Rebuild a witness from its JSON representation.

    An absent year stays absent. Reading it as a zero would let a text with
    no stated identity acquire one on the way back in.

    Args:
        payload: A dictionary previously produced by `_witness_dict`.

    Returns:
        The reconstructed witness.
    """
    edition = payload["edition"]
    return Witness(
        work=str(payload["work"]),
        origin=str(payload["origin"]),
        fidelity=Fidelity(payload["fidelity"]),
        edition=Edition(
            statement=_text_or_none(edition["statement"]),
            stated_year=_int_or_none(edition["stated_year"]),
            impression=_text_or_none(edition["impression"]),
            copyright_year=_int_or_none(edition["copyright_year"]),
        ),
    )


def _text_or_none(value: Any) -> str | None:
    """Read an optional string field, keeping `null` distinct from empty.

    Args:
        value: The stored value.

    Returns:
        The value as text, or None when the file stored `null`.
    """
    return None if value is None else str(value)


def _int_or_none(value: Any) -> int | None:
    """Read an optional whole number, keeping `null` distinct from zero.

    A year the front matter never printed and a count nobody recorded are
    both absences, and neither is a zero.

    Args:
        value: The stored value.

    Returns:
        The value as a whole number, or None when the file stored `null`.
    """
    return None if value is None else int(value)


def _as_dict(preparation: Preparation) -> dict[str, Any]:
    """Render a preparation as JSON-safe primitives.

    `concept` is written for a reader's convenience. It is derived from the
    surface forms, so the loader recomputes it rather than trusting the file.
    The reference carries its fidelity, so one record lifted out of the file
    still says which text its line number points into.

    Args:
        preparation: The preparation to render.

    Returns:
        A dictionary of JSON-safe values.
    """
    return {
        "concept": preparation.concept,
        "title": preparation.title,
        "parent": preparation.parent,
        "terms": [
            {"surface": t.surface, "language": t.language.value, "concept": t.concept}
            for t in preparation.terms
        ],
        "ref": {
            "source_id": preparation.ref.source_id,
            "entry": preparation.ref.entry,
            "line": preparation.ref.line,
            "fidelity": preparation.ref.fidelity.value,
        },
        "body": preparation.body,
    }


def _from_dict(payload: dict[str, Any]) -> Preparation:
    """Rebuild a preparation from its JSON representation.

    A `parent` of `null` is unresolved. Any other falsy value is malformed,
    and raises rather than being read as an absence of evidence. An unknown
    fidelity raises for the same reason.

    Args:
        payload: A dictionary previously produced by `_as_dict`.

    Returns:
        The reconstructed preparation.
    """
    ref = payload["ref"]
    parent = payload["parent"]
    return Preparation(
        title=str(payload["title"]),
        terms=tuple(
            Term(surface=str(t["surface"]), language=Language(t["language"]))
            for t in payload["terms"]
        ),
        body=str(payload["body"]),
        ref=SourceRef(
            source_id=str(ref["source_id"]),
            entry=int(ref["entry"]),
            line=int(ref["line"]),
            fidelity=Fidelity(ref["fidelity"]),
        ),
        parent=None if parent is None else ConceptId(to_concept_id(str(parent))),
    )
