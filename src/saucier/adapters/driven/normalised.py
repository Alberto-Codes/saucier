"""Repair what a scanner did to the page, never to the words on it.

OCR of a printed page double-spaces words and puts a space before a colon.
Neither is a comprehension problem, and both stop the extraction patterns
matching: `CHAPTER  I ` fails the chapter test, and `basic  sauces :` fails
the mothers test. Three rules fix both.

It also breaks the em dash that separates an entry number from its title,
rendering it as one hyphen, as two, or as an underscore. `126-- MAYONNAISE
SAUCE` is entry 126 of the same book, and a reader that requires U+2014
cannot see it at all. Fifty-seven headings are lost that way, thirteen of
them sauces, and a comparison then reports them as sauces the later edition
added.

This is an adapter that wraps another adapter, so the rules live outside
every source and outside every service. ADR-0011 records why.

Nothing here repairs a word. The separator is punctuation that delimits a
record, and the licence to repair it comes from the same document: 2,663
lines in it carry the undamaged shape. Turning `velout^` back into `velouté`
is a different act, because the evidence for the missing letter is outside
the witness. ADR-0013 draws that line.

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

SEPARATOR = re.compile(r"^(\d{1,4})\s*(?:-{1,2}|_)\s*(.+)$")
"""A number, a broken separator, and a title.

The scan renders the em dash as one hyphen, as two, or as an underscore.
`126-- MAYONNAISE SAUCE`, `36 -DEVILLED SAUCE`, and `57_VENISON SAUCE` are
all entries of the same book.
"""

ENTRY_DASH = "—"
"""What the separator should have been. `extraction.ENTRY` requires it."""

LETTERS = re.compile(r"[A-Za-z]")
"""Letters only. A tail of digits and marks is not a title."""

SHORTEST_TITLE = 3
"""Letters a title must exceed. `1-^` is damage rather than a heading."""

OPENING_LETTERS = 4
"""Letters that must be capitals for a tail to read as a title.

Measured rather than chosen. Escoffier sets every heading in capitals and
every sentence in prose, so four is enough to separate them, and the whole
title cannot be required: `33- CHASSEUR SAUCE (Escoffier's Method)` is a
heading with a lower-case parenthetical and `684- VELOUTE DE HOMARD,
otherwise CARDINAL` is one with a lower-case joining word.
"""


def _opens_in_capitals(title: str) -> bool:
    """Test whether a tail reads as a heading rather than as a sentence.

    Args:
        title: The text after a broken separator.

    Returns:
        True if the title carries enough letters and opens in capitals.
    """
    letters = LETTERS.findall(title)
    if len(letters) <= SHORTEST_TITLE:
        return False
    return "".join(letters[:OPENING_LETTERS]).isupper()


def repair_separator(line: str) -> str:
    """Restore the em dash a scanner broke between a number and a title.

    Only where the line is unmistakably a heading. The title has to open in
    four capitals and carry more than three letters, which is what separates
    a heading from the numbered prose in the same book. `1. Ordinary and
    clarified consommes.` is a sentence, and it stays one.

    The repair consumes the separator and nothing else, so the title is the
    same bytes either way. `QRIBICHE` stays `QRIBICHE`, and the comparison is
    what notices it resembles `GRIBICHE`.

    Args:
        line: One line, its whitespace already regularised.

    Returns:
        The line with its separator restored, or unchanged when the line is
        not unmistakably a heading.
    """
    match = SEPARATOR.match(line)
    if not match or not _opens_in_capitals(match.group(2)):
        return line
    return f"{match.group(1)}{ENTRY_DASH}{match.group(2)}"


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
    maps every body line through `normalise` and then `repair_separator`.
    Both are idempotent, so wrapping a clean source is safe and wrapping
    twice changes nothing.

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
        """Return the wrapped body with every line cleaned and mended.

        Whitespace is regularised first, so the separator rule sees single
        spaces and can be written for one shape rather than several.

        Returns:
            Body lines in document order, one for each line the wrapped
            source yielded.
        """
        return [repair_separator(normalise(line)) for line in self.inner.lines()]
