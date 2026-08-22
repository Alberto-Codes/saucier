"""Where things live. One place, so no other module hardcodes a path.

Discovery walks up for a directory holding `corpus/`. It raises when it
finds none, rather than falling back to the working directory and reporting
a missing file under a path the caller never chose.

A source id is not configured here. The work name is, because a title page
names a book rather than a repository, and the edition year is read out of
the document. A corpus filename that agrees with the resulting id is a
convenience for a reader with a shell, and `tests/test_corpus.py` proves the
agreement rather than assuming it.

Examples:
    Locate the committed corpus from anywhere in the tree:

    ```python
    from saucier.infrastructure.config import Paths

    paths = Paths.discover()
    assert paths.escoffier_transcription.name == "escoffier-1909.txt"
    ```

See Also:
    - [saucier.infrastructure.bootstrap][]: What consumes these paths.
    - [saucier.domain.witness][]: What an id is built from.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from saucier.domain.errors import ProjectRootNotFound

ESCOFFIER = "escoffier"
"""Work name for Escoffier's 'A Guide to Modern Cookery'. The year is read."""

GUTENBERG_ORIGIN = "Project Gutenberg 71395"
"""Citable name of the proofread witness, recorded on every record it yields."""

GUTENBERG_URL = "https://www.gutenberg.org/cache/epub/71395/pg71395.txt"
"""Where the proofread witness came from, so the provenance is checkable."""

ARCHIVE_ITEM = "cu31924000610117"
"""Internet Archive item for the Cornell University Library copy of 1907."""

ARCHIVE_ORIGIN = f"Internet Archive {ARCHIVE_ITEM}"
"""Citable name of the scanned witness, recorded on every record it yields."""

ARCHIVE_URL = f"https://archive.org/download/{ARCHIVE_ITEM}/{ARCHIVE_ITEM}_djvu.txt"
"""Where the scanned witness came from. Cornell records no US restrictions."""

TRANSCRIPTION_FILE = "escoffier-1909.txt"
"""Corpus file holding the proofread transcription of the 1909 revision."""

SCAN_FILE = "escoffier-1907.txt"
"""Corpus file holding the OCR of the 1907 first printing."""


@dataclass(frozen=True, slots=True)
class Paths:
    """Filesystem layout for a saucier working tree.

    One property per committed witness, named for how the text was obtained
    rather than for the edition it holds. The edition is read out of the
    document, so a path may not claim to know it.

    Attributes:
        root (Path): Project root containing `corpus/` and `data/`.

    Examples:
        Resolve the corpus without hardcoding a path:

        ```python
        paths = Paths.discover()
        assert paths.corpus.is_dir()
        ```
    """

    root: Path

    @classmethod
    def discover(cls, start: Path | None = None) -> Paths:
        """Find the project root by walking up from a starting file.

        Args:
            start: File to walk up from, this module when omitted.

        Returns:
            Paths rooted at the directory containing `corpus/`.

        Raises:
            ProjectRootNotFound: If no ancestor holds `corpus/`. Saucier
                reads a committed corpus, so a tree without one is a
                situation to report, not to guess a root for.
        """
        here = (start or Path(__file__)).resolve()
        for parent in here.parents:
            if (parent / "corpus").is_dir():
                return cls(root=parent)
        msg = f"no corpus/ directory above {here}. Run saucier from a clone"
        raise ProjectRootNotFound(msg)

    @property
    def corpus(self) -> Path:
        """Directory holding committed source material."""
        return self.root / "corpus"

    @property
    def data(self) -> Path:
        """Directory holding derived output, reproducible and untracked."""
        return self.root / "data"

    @property
    def escoffier_transcription(self) -> Path:
        """The Escoffier text proofread by the Distributed Proofreaders."""
        return self.corpus / TRANSCRIPTION_FILE

    @property
    def escoffier_scan(self) -> Path:
        """The Escoffier text machine-read from a library scan."""
        return self.corpus / SCAN_FILE
