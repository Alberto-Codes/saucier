"""Read a Project Gutenberg plain-text ebook as a source document.

Examples:
    Open the committed corpus:

    ```python
    from pathlib import Path

    from saucier.adapters.driven.gutenberg import GutenbergText

    source = GutenbergText(Path("corpus/escoffier-1907.txt"), "escoffier-1907")
    body = source.lines()
    ```

See Also:
    - [saucier.ports.source][]: The contract this satisfies.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from saucier.domain.errors import SourceUnreadable

START = "*** START OF THE PROJECT GUTENBERG EBOOK"
END = "*** END OF THE PROJECT GUTENBERG EBOOK"


@dataclass(frozen=True, slots=True)
class GutenbergText:
    """A Gutenberg ebook on disk, with its licence wrapper stripped.

    Gutenberg wraps public-domain text in its own licence header and footer.
    The wrapper stays in the committed file, because redistributing it is the
    courteous thing to do, and is removed here so no extractor ever sees it.

    Attributes:
        path (Path): Location of the downloaded ebook.
        source_id (str): Stable identifier used in every reference to this
            source.

    Examples:
        Read the body with the licence wrapper already removed:

        ```python
        source = GutenbergText(Path("corpus/escoffier-1907.txt"), "escoffier-1907")
        assert not source.lines()[0].startswith("The Project Gutenberg")
        ```
    """

    path: Path
    source_id: str

    def lines(self) -> list[str]:
        """Return the ebook body, licence wrapper removed.

        Returns:
            Body lines in document order, without trailing newlines.

        Raises:
            SourceUnreadable: If the file is missing, or carries no Gutenberg
                start marker, which means it is not the file we expect.
        """
        try:
            raw = self.path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            msg = f"cannot read source at {self.path}"
            raise SourceUnreadable(msg) from exc

        opening = _index_of(raw, START)
        if opening is None:
            msg = f"no Gutenberg start marker in {self.path}"
            raise SourceUnreadable(msg)
        closing = _index_of(raw, END) or len(raw)
        return raw[opening + 1 : closing]


def _index_of(lines: list[str], marker: str) -> int | None:
    """Find the first line beginning with a marker.

    Args:
        lines: Lines to search.
        marker: Literal prefix to look for.

    Returns:
        The index of the first matching line, or None when absent.
    """
    for index, line in enumerate(lines):
        if line.startswith(marker):
            return index
    return None
