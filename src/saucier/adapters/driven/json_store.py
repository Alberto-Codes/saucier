"""Persist catalogues as JSON files.

JSON while a human still checks the parser's work by eye. It stops being the
right answer the moment appending one record means rewriting the file.

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
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from saucier.domain.errors import SourceUnreadable
from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
from saucier.domain.types import ConceptId, Language


@dataclass(frozen=True, slots=True)
class JsonCatalogueStore:
    """A directory of catalogue JSON files, one per source.

    Attributes:
        directory (Path): Where catalogue files are written.

    Examples:
        One file per source, named for it:

        ```python
        store = JsonCatalogueStore(Path("data"))
        store.save(catalogue)  # writes data/escoffier-1907.json
        ```
    """

    directory: Path

    def _path_for(self, source_id: str) -> Path:
        """Resolve the file backing one source's catalogue.

        Args:
            source_id: Identifier of the source.

        Returns:
            Path to that source's catalogue file.
        """
        return self.directory / f"{source_id}.json"

    def save(self, catalogue: Catalogue) -> None:
        """Write a catalogue, replacing any previous one for its source.

        Args:
            catalogue: The catalogue to persist.
        """
        self.directory.mkdir(parents=True, exist_ok=True)
        payload = {
            "source_id": catalogue.source_id,
            "mothers": sorted(catalogue.mothers),
            "preparations": [_as_dict(p) for p in catalogue.preparations],
        }
        self._path_for(catalogue.source_id).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    def load(self, source_id: str) -> Catalogue:
        """Read back a previously saved catalogue.

        Args:
            source_id: Identifier of the source whose catalogue to load.

        Returns:
            The stored catalogue.

        Raises:
            SourceUnreadable: If no catalogue is stored for that source.
        """
        path = self._path_for(source_id)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            msg = f"no catalogue stored for {source_id} at {path}"
            raise SourceUnreadable(msg) from exc
        return Catalogue(
            source_id=payload["source_id"],
            preparations=tuple(_from_dict(p) for p in payload["preparations"]),
            mothers=frozenset(ConceptId(m) for m in payload["mothers"]),
        )


def _as_dict(preparation: Preparation) -> dict[str, Any]:
    """Render a preparation as JSON-safe primitives.

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
        },
        "body": preparation.body,
    }


def _from_dict(payload: dict[str, Any]) -> Preparation:
    """Rebuild a preparation from its JSON representation.

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
            Term(
                surface=str(t["surface"]),
                language=Language(t["language"]),
                concept=ConceptId(str(t["concept"])),
            )
            for t in payload["terms"]
        ),
        body=str(payload["body"]),
        ref=SourceRef(
            source_id=str(ref["source_id"]),
            entry=int(ref["entry"]),
            line=int(ref["line"]),
        ),
        parent=ConceptId(str(parent)) if parent else None,
    )
