"""Wiring. Builds concrete adapters and hands them to the services.

Factories return their port type rather than the concrete class, so callers
depend on the contract and swapping an implementation touches this module
only.

The corpus holds two witnesses of one work. The proofread transcription
carries a Gutenberg wrapper and needs no cleaning. The scan carries no
wrapper and is wrapped in `NormalisedText`, which is where a reader can see
which source is normalised and which is not.

Examples:
    Wire the defaults and extract every witness:

    ```python
    from saucier.infrastructure.bootstrap import catalogue_store, escoffier_sources
    from saucier.services.extraction import extract

    for source in escoffier_sources():
        catalogue_store().save(extract(source))
    ```

See Also:
    - [saucier.adapters][]: The implementations chosen here.
"""

from __future__ import annotations

from saucier.adapters.driven.gutenberg import GutenbergText
from saucier.adapters.driven.json_store import JsonCatalogueStore
from saucier.adapters.driven.normalised import NormalisedText
from saucier.adapters.driven.plain_text import PlainText
from saucier.domain.witness import Fidelity
from saucier.infrastructure.config import (
    ARCHIVE_ORIGIN,
    ESCOFFIER,
    GUTENBERG_ORIGIN,
    Paths,
)
from saucier.ports.source import SourceText
from saucier.ports.store import CatalogueStore


def escoffier_sources(paths: Paths | None = None) -> tuple[SourceText, ...]:
    """Build every Escoffier witness the corpus holds.

    The revised edition comes first, because it is the one the published
    census describes and the one the other commands default to.

    Args:
        paths: Filesystem layout to use, discovered when omitted.

    Returns:
        One source adapter per committed witness, revision first.
    """
    resolved = paths or Paths.discover()
    return (
        GutenbergText(
            path=resolved.escoffier_transcription,
            work=ESCOFFIER,
            origin=GUTENBERG_ORIGIN,
            fidelity=Fidelity.TRANSCRIPTION,
        ),
        NormalisedText(
            inner=PlainText(
                path=resolved.escoffier_scan,
                work=ESCOFFIER,
                origin=ARCHIVE_ORIGIN,
                fidelity=Fidelity.OCR,
            )
        ),
    )


def default_source_id(paths: Paths | None = None) -> str:
    """Name the witness a lookup reads when the caller names none.

    Read from the first configured witness rather than written down, so no
    module carries a second copy of an identifier the document decides.

    Args:
        paths: Filesystem layout to use, discovered when omitted.

    Returns:
        The source id of the first committed witness.
    """
    return escoffier_sources(paths)[0].witness.source_id


def catalogue_store(paths: Paths | None = None) -> CatalogueStore:
    """Build the catalogue store adapter.

    Args:
        paths: Filesystem layout to use, discovered when omitted.

    Returns:
        A store writing catalogue JSON under `data/`.
    """
    resolved = paths or Paths.discover()
    return JsonCatalogueStore(directory=resolved.data)
