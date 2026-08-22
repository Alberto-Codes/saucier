"""Clean the whitespace a scanner leaves behind, without touching a letter.

OCR of a printed page double-spaces words and puts a space before a colon.
Neither is a comprehension problem, and both stop the extraction patterns
matching: `CHAPTER  I ` fails the chapter test, and `basic  sauces :` fails
the mothers test. Three rules fix both.

This is an adapter that wraps another adapter, so the rules live outside
every source and outside every service. ADR-0011 records why.

Nothing here repairs a character. Turning `velout^` back into `velouté`
would manufacture agreement between the two witnesses this corpus compares.

Examples:
    Wrap a scanned source before extracting from it:

    ```python
    from saucier.adapters.driven.normalised import NormalisedText

    source = NormalisedText(inner=PlainText(...))
    assert "  " not in source.lines()[0]
    ```

See Also:
    - [saucier.ports.source][]: The contract this satisfies and consumes.
    - [saucier.adapters.driven.plain_text][]: The usual thing to wrap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from saucier.domain.witness import Witness
from saucier.ports.source import SourceText

RUNS = re.compile(r"[ \t]+")
"""A scan double-spaces words, and every pattern here counts single spaces."""

BEFORE_PUNCTUATION = re.compile(r"\s+([:;,.])")
"""A scan sets a space before a colon, which the mothers pattern will not match."""


def normalise(line: str) -> str:
    """Clean one line of scanning artefacts.

    Collapses runs of spaces and tabs, removes the space before punctuation,
    and trims the ends. Every rule maps one line to one line, so a recorded
    line number still names a line in the file on disk.

    Args:
        line: One line as the scan produced it.

    Returns:
        The same line with its whitespace regularised.
    """
    return BEFORE_PUNCTUATION.sub(r"\1", RUNS.sub(" ", line)).strip()


@dataclass(frozen=True, kw_only=True)
class NormalisedText:
    """A source whose lines are cleaned before any extractor reads them.

    The wrapper delegates identity and offset to the source it wraps, and
    maps every body line through `normalise`. Normalisation is idempotent, so
    wrapping a clean source is safe and wrapping twice changes nothing.

    Attributes:
        inner (SourceText): The source whose lines need cleaning.

    Examples:
        Identity comes from the wrapped source, unchanged:

        ```python
        assert NormalisedText(inner=source).witness == source.witness
        ```
    """

    inner: SourceText

    @property
    def witness(self) -> Witness:
        """What the wrapped text is.

        Returns:
            The wrapped source's witness, unchanged. Cleaning whitespace does
            not change which edition a document states.
        """
        return self.inner.witness

    @property
    def line_offset(self) -> int:
        """Count of file lines removed from the front of the body.

        Returns:
            The wrapped source's offset. No line is added or dropped here.
        """
        return self.inner.line_offset

    def lines(self) -> list[str]:
        """Return the wrapped body with every line cleaned.

        Returns:
            Body lines in document order, one for each line the wrapped
            source yielded.
        """
        return [normalise(line) for line in self.inner.lines()]
