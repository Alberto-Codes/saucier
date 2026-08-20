"""Wiring. Builds concrete adapters and hands them to the services.

Factories return their port type rather than the concrete class, so callers
depend on the contract and swapping an implementation touches this module
only.

Examples:
    Wire the defaults and extract:

    ```python
    from saucier.infrastructure.bootstrap import catalogue_store, escoffier_source
    from saucier.services.extraction import extract

    catalogue = extract(escoffier_source())
    catalogue_store().save(catalogue)
    ```

See Also:
    - [saucier.adapters][]: The implementations chosen here.
"""

from __future__ import annotations

from saucier.adapters.driven.gutenberg import GutenbergText
from saucier.adapters.driven.json_store import JsonCatalogueStore
from saucier.infrastructure.config import ESCOFFIER, Paths
from saucier.ports.source import SourceText
from saucier.ports.store import CatalogueStore


def escoffier_source(paths: Paths | None = None) -> SourceText:
    """Build the Escoffier source adapter.

    Args:
        paths: Filesystem layout to use, discovered when omitted.

    Returns:
        A source adapter reading the committed Escoffier text.
    """
    resolved = paths or Paths.discover()
    return GutenbergText(path=resolved.escoffier, source_id=ESCOFFIER)


def catalogue_store(paths: Paths | None = None) -> CatalogueStore:
    """Build the catalogue store adapter.

    Args:
        paths: Filesystem layout to use, discovered when omitted.

    Returns:
        A store writing catalogue JSON under `data/`.
    """
    resolved = paths or Paths.discover()
    return JsonCatalogueStore(directory=resolved.data)
