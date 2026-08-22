"""Read the edition a source states about itself.

A printed book records its own printing history on the title page verso.
Escoffier's runs from `First Printed, May 1907` to `January 1920`, and names
the revision in the middle of it. That block is evidence in exactly the way
the mothers sentence is evidence, so it is read rather than configured.

The reader walks the head of the body, collects every printing it finds, and
keeps three facts apart. The last printing naming an edition is the edition.
The last printing of all is the impression, because that is the copy in hand.
The copyright line is neither.

Examples:
    Read what a title page states:

    ```python
    from saucier.services.front_matter import read_edition

    edition = read_edition(source.lines())
    print(edition.statement, edition.impression)
    ```

See Also:
    - [saucier.domain.witness][]: The value this module builds.
    - [saucier.services.extraction][]: The other reader of the same text.
"""

from __future__ import annotations

import re
from typing import NamedTuple

from saucier.domain.errors import EditionUnstated
from saucier.domain.witness import Edition

FRONT_MATTER = 400
"""Body lines to read while looking for a title page.

Escoffier's title page sits 95 lines into the Gutenberg body and 182 lines
into the Archive scan, which carries a library plate and a page of adverts
first. A date deeper than this is prose, not a printing history.
"""

DATE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September"
    r"|October|November|December)\s+(\d{4})\b"
)
"""A printing date. The history gives every printing a month and a year."""

COPYRIGHT = re.compile(r"\bCopyright\s+(\d{4})\b", re.IGNORECASE)
"""The copyright line, which names a year and never an edition."""

EDITION_WORD = re.compile(r"\bedition\b", re.IGNORECASE)
"""A printing labelled as an edition is a revision, not another impression."""

FURNITURE = " _*"
"""Emphasis and rules the transcriber wraps a printing history in."""


class Printing(NamedTuple):
    """One printing the front matter records.

    Attributes:
        label (str): How the history names it, such as `New and Revised
            Edition`.
        date (str): Month and year, such as `January 1909`.
        year (int): The year of that date.
    """

    label: str
    date: str
    year: int


def _printings(lines: list[str]) -> list[Printing]:
    """Collect every printing the head of a source records.

    A printing history runs its label and its dates across lines. `New
    Impressions, August 1911, May 1913,` continues onto the next line, so a
    line opening with a date inherits the label above it.

    Args:
        lines: The source body as lines.

    Returns:
        Printings in the order the history presents them.
    """
    found: list[Printing] = []
    label = ""
    for line in lines[:FRONT_MATTER]:
        text = line.strip(FURNITURE)
        if not DATE.search(text):
            continue
        head = text.split(",")[0].strip(FURNITURE)
        if head and not DATE.search(head):
            label = head
        found.extend(
            Printing(label=label, date=match.group(0), year=int(match.group(2)))
            for match in DATE.finditer(text)
        )
    return found


def _copyright_year(lines: list[str]) -> int | None:
    """Read the copyright year the front matter prints.

    Args:
        lines: The source body as lines.

    Returns:
        The first copyright year found, or None when none is printed.
    """
    for line in lines[:FRONT_MATTER]:
        # The transcriber wraps the line in emphasis, and `_Copyright` has no
        # word boundary in front of the C.
        match = COPYRIGHT.search(line.strip(FURNITURE))
        if match:
            return int(match.group(1))
    return None


def read_edition(lines: list[str]) -> Edition:
    """Read the edition a source states on its own title page.

    Args:
        lines: The source body as lines, packaging already removed.

    Returns:
        What the front matter states, with the edition, the impression, and
        the copyright year recorded apart from each other.

    Raises:
        EditionUnstated: If the head of the source names neither an edition
            nor a copyright year. A text with no stated identity is reported
            rather than named from its path.
    """
    printings = _printings(lines)
    revisions = [p for p in printings if EDITION_WORD.search(p.label)]
    latest = revisions[-1] if revisions else None
    try:
        return Edition(
            statement=f"{latest.label}, {latest.date}" if latest else None,
            stated_year=latest.year if latest else None,
            impression=printings[-1].date if printings else None,
            copyright_year=_copyright_year(lines),
        )
    except EditionUnstated as exc:
        msg = f"no edition and no copyright year in the first {FRONT_MATTER} lines"
        raise EditionUnstated(msg) from exc
