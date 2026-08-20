"""Port for reading a source document.

Examples:
    Anything answering this shape can be extracted from:

    ```python
    from saucier.services.extraction import extract

    catalogue = extract(source)
    ```

See Also:
    - [saucier.adapters.driven.gutenberg][]: The implementation in use.
"""

from __future__ import annotations

from typing import Protocol


class SourceText(Protocol):
    """A source document the extractor can read.

    Implementations strip whatever packaging their format carries — licence
    headers, front matter, page furniture — and return only the body an
    extractor should see.

    Examples:
        Any object of this shape satisfies the port:

        ```python
        class Fixture:
            source_id = "fixture"

            def lines(self) -> list[str]:
                return ["22—BROWN SAUCE", "body"]
        ```
    """

    @property
    def source_id(self) -> str:
        """Stable identifier for this source document."""
        ...

    def lines(self) -> list[str]:
        """Return the document body as lines, packaging removed.

        Returns:
            Body lines in document order, without trailing newlines.
        """
        ...
