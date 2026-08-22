"""Read a Project Gutenberg plain-text ebook as a source document.

The file is read once and held. Provenance needs three things from it: the
body an extractor should see, the count of licence-header lines removed
before it, and the edition the front matter states.

The reader refuses a file carrying no Gutenberg markers. That refusal is the
point of the adapter. A source in another format gets its own adapter rather
than a looser marker test here.

Examples:
    Open the committed corpus:

    ```python
    from pathlib import Path

    from saucier.adapters.driven.gutenberg import GutenbergText
    from saucier.domain.witness import Fidelity

    source = GutenbergText(
        path=Path("corpus/escoffier-1909.txt"),
        work="escoffier",
        origin="Project Gutenberg 71395",
        fidelity=Fidelity.TRANSCRIPTION,
    )
    body = source.lines()
    ```

See Also:
    - [saucier.ports.source][]: The contract this satisfies.
    - [saucier.adapters.driven.plain_text][]: The reader for a file with no
      wrapper to strip.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from saucier.domain.errors import SourceUnreadable
from saucier.domain.witness import Fidelity, Witness
from saucier.services.front_matter import read_edition

START = "*** START OF THE PROJECT GUTENBERG EBOOK"
END = "*** END OF THE PROJECT GUTENBERG EBOOK"


@dataclass(frozen=True, kw_only=True)
class GutenbergText:
    """A Gutenberg ebook on disk, with its licence wrapper stripped.

    Gutenberg wraps public-domain text in its own licence header and footer.
    The wrapper stays in the committed file, because redistributing it is the
    courteous thing to do, and is removed here so no extractor ever sees it.
    The file is read once and the result is held, because provenance asks for
    the body and the offset separately.

    Attributes:
        path (Path): Location of the downloaded ebook.
        work (str): Name of the book across its editions. The edition year is
            read from the text, so the two together give the source id.
        origin (str): Where the text was obtained, citable by a reader.
        fidelity (Fidelity): How the text was obtained.

    Examples:
        Read the body with the licence wrapper already removed:

        ```python
        assert not source.lines()[0].startswith("The Project Gutenberg")
        ```
    """

    path: Path
    work: str
    origin: str
    fidelity: Fidelity

    @cached_property
    def _body(self) -> tuple[int, list[str]]:
        """Read the file and locate the body inside its licence wrapper.

        Returns:
            The count of file lines before the body, and the body lines.

        Raises:
            SourceUnreadable: If the file is missing, is not UTF-8 text, or
                carries no Gutenberg markers, which means it is not the file
                we expect.
        """
        try:
            raw = self.path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            msg = f"cannot read source at {self.path}"
            raise SourceUnreadable(msg) from exc
        except UnicodeDecodeError as exc:
            msg = f"source at {self.path} is not UTF-8 text"
            raise SourceUnreadable(msg) from exc

        opening = _index_of(raw, START)
        if opening is None:
            msg = f"no Gutenberg start marker in {self.path}"
            raise SourceUnreadable(msg)
        closing = _index_of(raw, END)
        if closing is None:
            msg = f"no Gutenberg end marker in {self.path}, so the file is truncated"
            raise SourceUnreadable(msg)
        return opening + 1, raw[opening + 1 : closing]

    @cached_property
    def witness(self) -> Witness:
        """What this text is, read from its own front matter.

        Returns:
            The witness, whose source id derives from the stated edition.

        Raises:
            SourceUnreadable: If the file cannot be read.
            EditionUnstated: If the front matter states no edition and no
                copyright year.
        """
        return Witness(
            work=self.work,
            origin=self.origin,
            fidelity=self.fidelity,
            edition=read_edition(self.lines()),
        )

    @property
    def line_offset(self) -> int:
        """Count of file lines removed from the front of the body.

        Returns:
            The number of licence header lines the reader skipped.
        """
        return self._body[0]

    def lines(self) -> list[str]:
        """Return the ebook body, licence wrapper removed.

        Returns:
            Body lines in document order, without trailing newlines.

        Raises:
            SourceUnreadable: If the file is missing, is not UTF-8 text, or
                carries no Gutenberg markers.
        """
        return list(self._body[1])


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
