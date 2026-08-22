"""Port for reading a source document.

Two implementations satisfy it. `GutenbergText` strips a licence wrapper and
refuses a file that carries no markers. `PlainText` reads a file that has no
wrapper at all. `NormalisedText` satisfies the port and consumes it, wrapping
either one to clean the whitespace a scanner leaves behind.

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

from saucier.domain.witness import Witness


class SourceText(Protocol):
    """A source document the extractor can read.

    Implementations strip whatever packaging their format carries, such as a
    licence header or page furniture, and return only the body an extractor
    should see. Each one also reports the witness it is: which edition the
    text states, and how the text was obtained.

    Examples:
        Any object of this shape satisfies the port:

        ```python
        class Fixture:
            witness = a_witness
            line_offset = 0

            def lines(self) -> list[str]:
                return ["22—BROWN SAUCE", "body"]
        ```
    """

    @property
    def witness(self) -> Witness:
        """What this text is, and how this project came by it.

        The `source_id` derives from the edition the document states, so a
        filename that happens to agree is a coincidence rather than evidence.
        """
        ...

    @property
    def line_offset(self) -> int:
        """Count of file lines removed from the front of the body.

        Added to a body index to name a line in the file on disk, so a
        reader can open the source and check a claim by hand.
        """
        ...

    def lines(self) -> list[str]:
        """Return the document body as lines, packaging removed.

        Returns:
            Body lines in document order, without trailing newlines.
        """
        ...
