"""Port for persisting an extracted catalogue.

Examples:
    Save and read back through the contract rather than an implementation:

    ```python
    store.save(catalogue)
    restored = store.load(catalogue.source_id)
    ```

See Also:
    - [saucier.adapters.driven.json_store][]: The implementation in use.
"""

from __future__ import annotations

from typing import Protocol

from saucier.domain.models import Catalogue


class CatalogueStore(Protocol):
    """Somewhere an extracted catalogue can be written and read back.

    Examples:
        Persist and restore through the contract:

        ```python
        where = store.save(catalogue)
        assert store.load(catalogue.source_id) == catalogue
        ```
    """

    def save(self, catalogue: Catalogue) -> str:
        """Persist a catalogue, replacing any previous one for its source.

        Args:
            catalogue: The catalogue to persist.

        Returns:
            Where the catalogue went, for a caller to report. A path for a
            file store, and whatever names the destination for any other.
        """
        ...

    def load(self, source_id: str) -> Catalogue:
        """Read back a previously saved catalogue.

        Args:
            source_id: Identifier of the source whose catalogue to load.

        Returns:
            The stored catalogue.

        Raises:
            SourceUnreadable: If no catalogue is stored for that source.
        """
        ...
