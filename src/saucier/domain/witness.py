"""What a text is: which edition it prints, and how it was obtained.

One work has many editions. One edition has many printings. This project
reads one text of one printing, and that text is a witness to the work
rather than the work itself. A proofread transcription and a raw scan of the
same page are two witnesses of unequal quality, and every record says which
one it came through.

The identity is read rather than configured. `Edition` records what a title
page states, keeping the edition, the impression, and the copyright year
apart, because one string cannot carry three facts.

Examples:
    Name a source from what its front matter states:

    ```python
    from saucier.domain.witness import Edition, Fidelity, Witness

    edition = Edition(
        statement="New and Revised Edition, January 1909",
        stated_year=1909,
        impression="January 1920",
        copyright_year=1907,
    )
    witness = Witness(
        work="escoffier",
        origin="Project Gutenberg 71395",
        fidelity=Fidelity.TRANSCRIPTION,
        edition=edition,
    )
    assert witness.source_id == "escoffier-1909"
    ```

See Also:
    - [saucier.services.front_matter][]: What reads an `Edition` from a text.
    - [saucier.domain.models][]: The records a witness stamps itself onto.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from saucier.domain.errors import EditionUnstated


class Fidelity(StrEnum):
    """How a witness was obtained, and therefore how far a surface is trusted.

    Stated, never inferred. Fidelity is a fact about acquisition rather than
    about the text, so it is recorded beside the URL the text came from. No
    code reads it off the characters.

    Examples:
        Members carry their recorded value:

        ```python
        assert Fidelity.OCR == "ocr"
        ```
    """

    TRANSCRIPTION = "transcription"
    OCR = "ocr"


@dataclass(frozen=True, slots=True, kw_only=True)
class Edition:
    """What a title page states about which printing a text is.

    Keyword-only, because three of the four fields are years or dates and a
    transposition would misname an edition while still type-checking.

    Attributes:
        statement (str | None): The edition line, verbatim, or None when the
            front matter names no edition.
        stated_year (int | None): Year of that statement, or None with none
            stated.
        impression (str | None): The last printing the history records, or
            None when it records none.
        copyright_year (int | None): Year on the copyright line, or None when
            the front matter carries none.

    Examples:
        A first printing states no edition, so its year is the copyright year:

        ```python
        first = Edition(
            statement=None, stated_year=None, impression=None, copyright_year=1907
        )
        assert first.year == 1907
        assert not first.stated
        ```
    """

    statement: str | None
    stated_year: int | None
    impression: str | None
    copyright_year: int | None

    def __post_init__(self) -> None:
        """Reject an edition that names no year at all.

        Raises:
            EditionUnstated: If neither a stated year nor a copyright year is
                present. A text with no stated identity cannot be given one
                from its path.
        """
        if self.stated_year is None and self.copyright_year is None:
            msg = "front matter states neither an edition year nor a copyright year"
            raise EditionUnstated(msg)

    @property
    def stated(self) -> bool:
        """Whether the front matter names an edition of its own.

        Returns:
            True when a printing history names an edition.
        """
        return self.statement is not None

    @property
    def year(self) -> int:
        """The year this text is identified by.

        A revision announces itself in the printing history, so a stated
        edition decides the year. A first printing has no history to print,
        so its copyright year decides it.

        Returns:
            The stated edition year, falling back to the copyright year.
        """
        if self.stated_year is not None:
            return self.stated_year
        # `__post_init__` rejects an edition with neither year, so the
        # copyright year is present here.
        return int(self.copyright_year or 0)


@dataclass(frozen=True, slots=True, kw_only=True)
class Witness:
    """One text of one edition, and how this project came by it.

    Attributes:
        work (str): Name of the book across its editions, such as
            `escoffier`. Configured, because a title page names a book rather
            than a repository.
        origin (str): Where the text was obtained, citable by a reader, such
            as `Project Gutenberg 71395`.
        fidelity (Fidelity): How the text was obtained.
        edition (Edition): What the front matter states about the printing.

    Examples:
        The source id is the work and the edition year, joined:

        ```python
        assert witness.source_id == f"{witness.work}-{witness.edition.year}"
        ```
    """

    work: str
    origin: str
    fidelity: Fidelity
    edition: Edition

    def __post_init__(self) -> None:
        """Reject a witness that cannot name itself.

        Raises:
            ValueError: If the work name or the origin is blank. Either one
                blank yields a source id or a citation no reader can follow.
        """
        if not self.work.strip() or not self.origin.strip():
            msg = (
                f"a witness needs a work and an origin: {self.work!r}, {self.origin!r}"
            )
            raise ValueError(msg)

    @property
    def source_id(self) -> str:
        """Stable identifier for this text.

        Returns:
            The work name and the edition year, joined by a hyphen.
        """
        return f"{self.work}-{self.edition.year}"
