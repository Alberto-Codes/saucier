"""Read a plain text file that carries no packaging to remove.

The Internet Archive publishes a scanned book as `<item>_djvu.txt`: the OCR
of every page, front matter included, with no wrapper of its own. Nothing is
stripped, so the body is the file and a recorded line number is a line in it.

This adapter exists because `GutenbergText` refuses a file with no Gutenberg
markers, and that refusal is correct. A second format gets a second adapter
rather than a looser test in the first one.

Examples:
    Open a scanned source:

    ```python
    from pathlib import Path

    from saucier.adapters.driven.plain_text import PlainText
    from saucier.domain.witness import Fidelity

    source = PlainText(
        path=Path("corpus/escoffier-1907.txt"),
        work="escoffier",
        origin="Internet Archive cu31924000610117",
        fidelity=Fidelity.OCR,
    )
    ```

See Also:
    - [saucier.ports.source][]: The contract this satisfies.
    - [saucier.adapters.driven.normalised][]: What a scanned source is
      usually wrapped in.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from saucier.domain.errors import SourceUnreadable
from saucier.domain.witness import Fidelity, Witness
from saucier.services.front_matter import read_edition


@dataclass(frozen=True, kw_only=True)
class PlainText:
    """A whole text file, read as the body an extractor should see.

    Attributes:
        path (Path): Location of the file.
        work (str): Name of the book across its editions. The edition year is
            read from the text, so the two together give the source id.
        origin (str): Where the text was obtained, citable by a reader.
        fidelity (Fidelity): How the text was obtained.

    Examples:
        The offset is zero, because nothing is stripped:

        ```python
        assert source.line_offset == 0
        ```
    """

    path: Path
    work: str
    origin: str
    fidelity: Fidelity

    @cached_property
    def _body(self) -> list[str]:
        """Read the whole file once and hold it.

        Returns:
            Every line of the file, without trailing newlines.

        Raises:
            SourceUnreadable: If the file is missing or is not UTF-8 text.
        """
        try:
            return self.path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            msg = f"cannot read source at {self.path}"
            raise SourceUnreadable(msg) from exc
        except UnicodeDecodeError as exc:
            msg = f"source at {self.path} is not UTF-8 text"
            raise SourceUnreadable(msg) from exc

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
            Zero. This format carries no packaging, so the body starts at the
            first line of the file.
        """
        return 0

    def lines(self) -> list[str]:
        """Return the file as body lines.

        Returns:
            Body lines in document order, without trailing newlines.

        Raises:
            SourceUnreadable: If the file is missing or is not UTF-8 text.
        """
        return list(self._body)
