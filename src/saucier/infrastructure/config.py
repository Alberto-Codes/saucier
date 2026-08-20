"""Where things live. One place, so no other module hardcodes a path.

Examples:
    Locate the committed corpus from anywhere in the tree:

    ```python
    from saucier.infrastructure.config import Paths

    paths = Paths.discover()
    assert paths.escoffier.name == "escoffier-1907.txt"
    ```

See Also:
    - [saucier.infrastructure.bootstrap][]: What consumes these paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ESCOFFIER = "escoffier-1907"
"""Source id for Escoffier's 'A Guide to Modern Cookery', Gutenberg 71395."""

GUTENBERG_URL = "https://www.gutenberg.org/cache/epub/71395/pg71395.txt"
"""Where the corpus came from, recorded so the provenance is checkable."""


@dataclass(frozen=True, slots=True)
class Paths:
    """Filesystem layout for a saucier working tree.

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
    def discover(cls) -> Paths:
        """Find the project root by walking up from this file.

        Returns:
            Paths rooted at the directory containing `corpus/`.
        """
        here = Path(__file__).resolve()
        for parent in here.parents:
            if (parent / "corpus").is_dir():
                return cls(root=parent)
        return cls(root=Path.cwd())

    @property
    def corpus(self) -> Path:
        """Directory holding committed source material."""
        return self.root / "corpus"

    @property
    def data(self) -> Path:
        """Directory holding derived output, reproducible and untracked."""
        return self.root / "data"

    @property
    def escoffier(self) -> Path:
        """The Escoffier source text."""
        return self.corpus / f"{ESCOFFIER}.txt"
