"""Frozen domain entities.

The model records what a source says, and how confidently it was read. It
does not record what the parser wishes were true: an unresolved parent is
`None`, never a guess.

The entities refuse states a source could not produce. A concept is derived
from its surface form rather than stored beside it, a reference has to name
a line a reader can open, and an unresolved parent is stated at every
construction site rather than defaulted.

Examples:
    Walk the derivations beneath a base preparation:

    ```python
    from saucier.domain.types import ConceptId

    for child in catalogue.children_of(ConceptId("espagnole")):
        print(child.title)
    ```

See Also:
    - [saucier.domain.types][]: The values these entities carry.
    - [saucier.services.extraction][]: What builds them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from saucier.domain.types import ConceptId, Language, to_concept_id


@dataclass(frozen=True, slots=True)
class Term:
    """A culinary term as it appears in one source, in one language.

    The concept is derived from the surface form, never stored beside it, so
    the two cannot contradict each other.

    Attributes:
        surface (str): The term exactly as written in the source.
        language (Language): The language the surface form is written in.

    Examples:
        Build a term and read the concept derived from it:

        ```python
        term = Term("Velouté", Language.FRENCH)
        assert term.concept == "veloute"
        ```
    """

    surface: str
    language: Language

    @property
    def concept(self) -> ConceptId:
        """Language-independent identifier for what the term denotes.

        Returns:
            The concept id folded from the surface form.
        """
        return to_concept_id(self.surface)


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceRef:
    """Where in a source a preparation was found.

    Keyword-only, because `entry` and `line` are both integers and a
    transposition would produce a citation that points at the wrong text
    while still type-checking.

    Attributes:
        source_id (str): Stable identifier for the source document.
        entry (int): The source's own numbering for the entry, 1 or greater.
        line (int): Line number in the source file where the entry begins,
            1 or greater, for hand-checking.

    Examples:
        Every preparation can be checked against the source by hand:

        ```python
        ref = SourceRef(source_id="escoffier-1907", entry=32, line=1680)
        print(ref.entry, ref.line)
        ```
    """

    source_id: str
    entry: int
    line: int

    def __post_init__(self) -> None:
        """Reject a reference that cannot be checked against a source.

        Raises:
            ValueError: If the source id is blank, or either number is below
                1, which would name a location no reader can open.
        """
        if not self.source_id.strip():
            msg = "a source reference needs a source id"
            raise ValueError(msg)
        if self.entry < 1 or self.line < 1:
            msg = f"entry and line must be 1 or greater: {self.entry}, {self.line}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class Preparation:
    """One numbered preparation as the source states it.

    `parent` carries no default. An absence of evidence is stated at every
    construction site, so a forgotten argument can never be mistaken for a
    reading of the source.

    Attributes:
        title (str): The entry heading, verbatim.
        terms (tuple[Term, ...]): Terms extracted from the heading, each
            language-tagged.
        body (str): The entry's prose, verbatim and unparsed.
        ref (SourceRef): Where this entry was found.
        parent (ConceptId | None): Concept this preparation derives from,
            when the source says so plainly. `None` means unresolved, never
            "probably none".

    Examples:
        An unresolved parent is absent rather than guessed:

        ```python
        if preparation.parent is None:
            print(f"{preparation.title} states no base")
        ```
    """

    title: str
    terms: tuple[Term, ...]
    body: str
    ref: SourceRef
    parent: ConceptId | None

    @property
    def concept(self) -> ConceptId:
        """Concept identifier for this preparation.

        Returns:
            The concept of the first extracted term, falling back to the
            folded title when the heading yielded no terms.
        """
        return self.terms[0].concept if self.terms else to_concept_id(self.title)


@dataclass(frozen=True, slots=True)
class Catalogue:
    """Every preparation read from one source, with the mothers named.

    Attributes:
        source_id (str): Identifier of the source these preparations came
            from.
        preparations (tuple[Preparation, ...]): Preparations in the order the
            source presents them.
        mothers (frozenset[ConceptId]): Concepts the source itself names as
            base preparations.

    Examples:
        Report how much of a source the parser could resolve:

        ```python
        print(f"{catalogue.unresolved} state no base in their prose")
        ```
    """

    source_id: str
    preparations: tuple[Preparation, ...] = field(default_factory=tuple)
    mothers: frozenset[ConceptId] = field(default_factory=frozenset)

    def by_concept(self) -> dict[ConceptId, Preparation]:
        """Index the preparations by every concept that names them.

        A preparation is reachable by any of its alternative names, so
        `BROWN SAUCE OR ESPAGNOLE` answers to both. When a source repeats a
        concept, the first occurrence wins.

        Returns:
            A mapping from concept id to preparation.
        """
        index: dict[ConceptId, Preparation] = {}
        for preparation in self.preparations:
            for term in preparation.terms:
                index.setdefault(term.concept, preparation)
            index.setdefault(preparation.concept, preparation)
        return index

    def matches(self, concept: ConceptId) -> tuple[Preparation, ...]:
        """Find every preparation a concept could name, best first.

        An exact hit wins outright. Otherwise the concept has to appear as a
        whole run of words inside a name, so `bordelaise` reaches
        `SAUCE BORDELAISE` but never `bordelaise-butter`. Candidates are
        ordered by how little else their name carries, then by the order the
        source presents them. Both signals come from the source: the least
        qualified name is the base, and Escoffier states a base before its
        derivatives.

        Args:
            concept: The concept to look for.

        Returns:
            Matching preparations, best match first, empty when none match.
        """
        index = self.by_concept()
        if concept in index:
            return (index[concept],)
        wanted = concept.split("-")
        order = {p.ref.entry: n for n, p in enumerate(self.preparations)}
        hits = []
        for name, found in index.items():
            parts = name.split("-")
            if _contains_run(parts, wanted):
                hits.append((len(parts), order[found.ref.entry], found))
        return tuple(found for _, _, found in sorted(hits, key=lambda h: h[:2]))

    def find(self, concept: ConceptId) -> Preparation | None:
        """Look up the preparation a concept names.

        Args:
            concept: The concept to look for.

        Returns:
            The best match, or None when nothing matches.
        """
        found = self.matches(concept)
        return found[0] if found else None

    def children_of(self, concept: ConceptId) -> tuple[Preparation, ...]:
        """Find preparations the source derives from a given concept.

        Args:
            concept: The parent concept to search for.

        Returns:
            Preparations whose recorded parent is that concept, in source
            order.
        """
        return tuple(p for p in self.preparations if p.parent == concept)

    @property
    def resolved(self) -> int:
        """Count preparations whose parent the parser resolved.

        Returns:
            The number of preparations with a non-null parent.
        """
        return sum(1 for p in self.preparations if p.parent is not None)

    @property
    def unresolved(self) -> int:
        """Count preparations that state no base in their prose.

        The published score. Defined once here so no caller derives it by
        its own subtraction.

        Returns:
            The number of preparations whose parent is None.
        """
        return len(self.preparations) - self.resolved


def _contains_run(parts: list[str], wanted: list[str]) -> bool:
    """Test whether one word run appears whole inside another.

    Args:
        parts: Words of the name being searched.
        wanted: Words of the concept being looked for.

    Returns:
        True if `wanted` appears as a contiguous run within `parts`.
    """
    span = len(wanted)
    return any(parts[i : i + span] == wanted for i in range(len(parts) - span + 1))
