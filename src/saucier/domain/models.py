"""Frozen domain entities.

The model records what a source says, and how confidently it was read. It
does not record what the parser wishes were true: an unresolved parent is
`None`, never a guess.

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

    Attributes:
        surface (str): The term exactly as written in the source.
        language (Language): The language the surface form is written in.
        concept (ConceptId): Language-independent identifier for what the
            term denotes.

    Examples:
        Build a term and read the concept derived from it:

        ```python
        term = Term.of("Velouté", Language.FRENCH)
        assert term.concept == "veloute"
        ```
    """

    surface: str
    language: Language
    concept: ConceptId

    @classmethod
    def of(cls, surface: str, language: Language) -> Term:
        """Build a term, deriving its concept id from the surface form.

        Args:
            surface: The term as written in the source.
            language: The language the surface form is written in.

        Returns:
            The term with its concept id derived.
        """
        return cls(surface=surface, language=language, concept=to_concept_id(surface))


@dataclass(frozen=True, slots=True)
class SourceRef:
    """Where in a source a preparation was found.

    Attributes:
        source_id (str): Stable identifier for the source document.
        entry (int): The source's own numbering for the entry.
        line (int): Line number where the entry begins, for hand-checking.

    Examples:
        Every preparation can be checked against the source by hand:

        ```python
        print(preparation.ref.entry, preparation.ref.line)
        ```
    """

    source_id: str
    entry: int
    line: int


@dataclass(frozen=True, slots=True)
class Preparation:
    """One numbered preparation as the source states it.

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
    parent: ConceptId | None = None

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
        unresolved = len(catalogue.preparations) - catalogue.resolved
        print(f"{unresolved} state no base in their prose")
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

    def find(self, concept: ConceptId) -> Preparation | None:
        """Look up a preparation, falling back to a name-ending match.

        Escoffier writes `SAUCE BORDELAISE`, so a reader asking for
        `bordelaise` should still find it.

        Args:
            concept: The concept to look for.

        Returns:
            The matching preparation, or None when nothing matches.
        """
        index = self.by_concept()
        if concept in index:
            return index[concept]
        suffixed = [c for c in sorted(index) if c.endswith(f"-{concept}")]
        return index[suffixed[0]] if suffixed else None

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
