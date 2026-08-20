"""Deterministic extraction of preparations from a numbered source.

No model runs here. Everything this module produces is traceable to a line
in the source, which is the point: it establishes how much structure the
source already carries, and therefore the bar any later model has to clear.

Extraction runs in two passes. The first reads the mothers, the sauce
chapters, and every kept entry. The second resolves each parent against
every name the first pass produced, so a parent may be any catalogued
preparation, and a chain of stated parents never cycles.

Examples:
    Read a catalogue and report what stayed unresolved:

    ```python
    from saucier.services.extraction import extract

    catalogue = extract(source)
    print(catalogue.unresolved)
    ```

See Also:
    - [saucier.domain.models][]: The entities produced.
    - [saucier.ports.source][]: The contract a source satisfies.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import replace
from typing import NamedTuple

from saucier.domain.errors import NoPreparationsFound
from saucier.domain.models import Catalogue, Preparation, SourceRef, Term, contains_run
from saucier.domain.types import ConceptId, Language, to_concept_id
from saucier.ports.source import SourceText

ENTRY = re.compile(r"^(\d{1,4})—(.+)$")
"""Escoffier numbers every preparation and joins it to its title with an em dash."""

MOTHERS = re.compile(r"basic sauces?:\s*(.+?)\.", re.IGNORECASE | re.DOTALL)
"""The source names its own base preparations; it is not our place to guess them."""

ALTERNATIVES = re.compile(r"\s+OR\s+", re.IGNORECASE)
"""Escoffier gives many preparations an English and a French name, joined by OR."""

CHAPTER = re.compile(r"^CHAPTER\s+[IVXL]+$")
"""The source divides itself into numbered chapters and titles each one."""

SAUCE_WORD = re.compile(r"\bSAUCES?\b", re.IGNORECASE)
"""Matches either number, for reading a chapter title."""

SAUCE = re.compile(r"\bSAUCE\b", re.IGNORECASE)
"""Singular only. A heading naming several sauces is describing a dish."""

SERVED_WITH = re.compile(r"\bWITH\b", re.IGNORECASE)
"""`ASPARAGUS WITH VARIOUS SAUCES` is a dish that takes a sauce, not a sauce."""

ACCOMPANIMENT = re.compile(r",\s*SAUCE\b", re.IGNORECASE)
"""`MAQUEREAU BOUILLI, SAUCE AUX GROSEILLES` names a dish and its sauce."""

CHAPTER_LOOKAHEAD = 6
"""Lines to read past a chapter marker while looking for its title."""

SEGMENT = re.compile(r"[.!?;:]")
"""Sentence boundaries. A name split across two sentences is not a statement."""

WORDED = re.compile(r"[a-zA-Z0-9]")
"""A segment with no letter or digit folds to nothing and is skipped."""

ASCII_MAX = 127
"""Above this codepoint a letter carries a diacritic the source kept.

Tested on letters only. The source also uses curly quotes and non-breaking
spaces, which say nothing about the language of the words around them.
"""

FRENCH_MARKERS = frozenset(
    {"espagnole", "veloute", "bechamel", "hollandaise", "roux", "glace-de-viande"}
)
"""Terms known to be French even when written without diacritics.

Tested word by word, because Escoffier writes `HOLLANDAISE SAUCE` as often as
he writes `HOLLANDAISE`.
"""


def _language_of(surface: str) -> Language:
    """Read the language a term is written in.

    Uses three signals: a letter carrying a diacritic, a heading beginning
    with `SAUCE ` (French word order, where English would put the word last),
    and a small lexicon of French terms that survive into English without
    their diacritics.

    Args:
        surface: The term as written.

    Returns:
        The language the term appears to be written in.
    """
    if any(ord(char) > ASCII_MAX for char in surface if char.isalpha()):
        return Language.FRENCH
    if surface.upper().startswith("SAUCE "):
        return Language.FRENCH
    words = to_concept_id(surface).split("-")
    return Language.FRENCH if FRENCH_MARKERS.intersection(words) else Language.ENGLISH


def terms_in(title: str) -> tuple[Term, ...]:
    """Split an entry heading into its language-tagged alternative names.

    Escoffier joins alternative names with `OR`. Trailing punctuation is
    trimmed from each name, commas included, so `AIOLI SAUCE, OR PROVENCE
    BUTTER` yields two clean surface forms.

    Args:
        title: The entry heading, verbatim.

    Returns:
        One term per alternative name in the heading, in heading order.
    """
    parts = (part.strip(" .,—") for part in ALTERNATIVES.split(title))
    return tuple(Term(part, _language_of(part)) for part in parts if part)


def find_mothers(body: str) -> frozenset[ConceptId]:
    """Read the base preparations the source names for itself.

    Args:
        body: The whole source body.

    Returns:
        Concepts the source calls basic sauces, empty if it names none.
    """
    match = MOTHERS.search(body)
    if not match:
        return frozenset()
    listed = re.split(r",|\band\b", match.group(1))
    return frozenset(to_concept_id(name.strip()) for name in listed if name.strip())


def sauce_chapters(lines: list[str]) -> tuple[tuple[int, int], ...]:
    """Read the line spans of the chapters the source titles as sauce chapters.

    The source classifies its own contents. Escoffier heads three chapters
    `THE LEADING WARM SAUCES`, `THE SMALL COMPOUND SAUCES`, and `COLD SAUCES
    AND COMPOUND BUTTERS`. Reading that is evidence, the same as reading the
    mothers out of the text. Guessing which chapter a soup belongs to is not.

    Args:
        lines: The source body as lines.

    Returns:
        Half-open spans of line indices, one per sauce chapter.
    """
    marks: list[tuple[int, bool]] = []
    for index, line in enumerate(lines):
        if not CHAPTER.match(line.strip()):
            continue
        titles = (
            n.strip().strip("=") for n in lines[index + 1 : index + CHAPTER_LOOKAHEAD]
        )
        title = next((t for t in titles if t), "")
        marks.append((index, bool(SAUCE_WORD.search(title))))
    spans = []
    for position, (start, is_sauce_chapter) in enumerate(marks):
        following = marks[position + 1][0] if position + 1 < len(marks) else len(lines)
        if is_sauce_chapter:
            spans.append((start, following))
    return tuple(spans)


def iter_entries(lines: list[str]) -> Iterator[tuple[int, int, str, str]]:
    """Walk the source, yielding one numbered entry at a time.

    Args:
        lines: The source body as lines.

    Yields:
        Tuples of entry number, index of the heading within `lines`, title,
        and body prose.
    """
    start: int | None = None
    number = 0
    title = ""
    for index, line in enumerate(lines):
        match = ENTRY.match(line)
        if not match:
            continue
        if start is not None:
            yield number, start, title, "\n".join(lines[start + 1 : index]).strip()
        number, title, start = int(match.group(1)), match.group(2).strip(), index
    if start is not None:
        yield number, start, title, "\n".join(lines[start + 1 :]).strip()


def names_a_sauce(title: str) -> bool:
    """Decide whether a heading calls its own preparation a sauce.

    The heading has to use the singular word, and use it before any `WITH`.
    `SOUBISE SAUCE WITH RICE` is a sauce served with something.
    `ASPARAGUS WITH VARIOUS SAUCES` is something served with a sauce. A
    heading that names its sauce after a comma is naming an accompaniment.

    Args:
        title: The entry heading.

    Returns:
        True if the heading itself says the entry is a sauce.
    """
    match = SAUCE.search(title)
    if match is None or ACCOMPANIMENT.search(title):
        return False
    served = SERVED_WITH.search(title)
    return served is None or match.start() < served.start()


def is_sauce(title: str, mothers: frozenset[ConceptId], in_sauce_chapter: bool) -> bool:
    """Decide whether an entry is a sauce this catalogue should carry.

    Two kinds of evidence qualify an entry, and nothing else does. The
    heading says "sauce". Or the heading names one of the mothers *and* the
    source filed the entry in a sauce chapter, which catches derivatives such
    as `LENTEN ESPAGNOLE` that never use the word. The chapter test is what
    keeps `TOMATO SALAD` and the velouté soups out.

    Args:
        title: The entry heading.
        mothers: Concepts the source names as base preparations.
        in_sauce_chapter: Whether the source filed this entry in a chapter it
            titles as sauces.

    Returns:
        True if the entry belongs in a sauce catalogue.
    """
    if names_a_sauce(title):
        return True
    if not in_sauce_chapter:
        return False
    return bool(mothers.intersection(to_concept_id(title).split("-")))


class Candidate(NamedTuple):
    """One name a stated parent may use, and what recording that name means.

    Attributes:
        key (int | ConceptId): Identity of the preparation the name reaches.
            The entry number when the name reaches a catalogued preparation,
            or the mother concept when the source declares a mother the
            catalogue cannot reach.
        records (ConceptId): The concept written into `parent` when this
            name decides the resolution.
        mother (bool): True when the name is a mother the source declares.
    """

    key: int | ConceptId
    records: ConceptId
    mother: bool


def parent_candidates(catalogue: Catalogue) -> dict[ConceptId, Candidate]:
    """Collect every name a stated parent may use.

    Every name comes from the source. The catalogue contributes each name of
    each preparation, and the source's own list of mothers contributes the
    mother concepts. Two names that reach one preparation share one key, so
    an opening naming both states one parent, not two.

    Args:
        catalogue: The catalogue whose preparations are the candidates.

    Returns:
        A mapping from each name to the candidate it states.
    """
    candidates = {
        name: Candidate(found.ref.entry, found.concept, mother=False)
        for name, found in catalogue.by_concept().items()
    }
    for declared in catalogue.mothers:
        found = catalogue.find(declared)
        key = found.ref.entry if found else declared
        candidates[declared] = Candidate(key, declared, mother=True)
    return candidates


def resolve_parent(
    body: str,
    own: frozenset[int | ConceptId],
    candidates: dict[ConceptId, Candidate],
) -> ConceptId | None:
    """Find the catalogued preparation an entry's prose derives it from.

    Only the opening paragraph counts. Escoffier states an ingredient list
    first, so a base named there is being used; a base named eight paragraphs
    later is usually being compared against, not built on. A name has to
    appear as a whole run of words inside one sentence, so `tomatoes` is not
    `tomato` and a name split across a full stop is not a statement.

    An entry naming no candidate resolves to `None`. So does an entry naming
    two: `SHRIMP SAUCE` says "fish velouté or, failing this, Béchamel", and
    picking one of those is a guess the source did not make. When the one
    stated parent was named as a mother, the mother concept is recorded, and
    otherwise the parent preparation's own concept is.

    Two further runs of words are not statements. A catalogued name inside
    the entry's own name denotes the entry's own subject, so `HORSE-RADISH
    SAUCE` naming horse-radish states an ingredient, not a parent. A mother
    is exempt, because a mother is never an entry's own subject, so `LENTEN
    ESPAGNOLE` naming Espagnole does state its base. And a name found only
    inside a longer stated name of another preparation is part of that
    statement, so `Lenten Espagnole` does not also state Espagnole.

    Args:
        body: The entry's prose.
        own: Keys and names that denote the entry itself, which cannot be
            its parent.
        candidates: Every name a stated parent may use.

    Returns:
        The parent concept, or None when the opening paragraph states no
        candidate or states more than one.
    """
    segments = _folded_segments(body.split("\n\n", 1)[0])
    own_names = [str(name).split("-") for name in own if not isinstance(name, int)]
    found: dict[ConceptId, tuple[Span, ...]] = {}
    for name, candidate in candidates.items():
        words = name.split("-")
        subject = not candidate.mother and any(
            contains_run(name, words) for name in own_names
        )
        if candidate.key in own or subject:
            continue
        spans = _spans(words, segments)
        if spans:
            found[name] = spans
    hits = [
        candidates[name] for name in found if not _shadowed(name, found, candidates)
    ]
    if len({hit.key for hit in hits}) != 1:
        return None
    stated_mothers = sorted(hit.records for hit in hits if hit.mother)
    return stated_mothers[0] if stated_mothers else hits[0].records


def _folded_segments(opening: str) -> tuple[list[str], ...]:
    """Fold an opening paragraph into sentence-bounded word runs.

    Args:
        opening: The opening paragraph, verbatim.

    Returns:
        One list of folded words per sentence that carries any.
    """
    return tuple(
        to_concept_id(segment).split("-")
        for segment in SEGMENT.split(opening)
        if WORDED.search(segment)
    )


Span = tuple[int, int, int]
"""Where a name was stated: segment index, first word, one past the last."""


def _spans(words: list[str], segments: tuple[list[str], ...]) -> tuple[Span, ...]:
    """Find every place a run of words appears whole inside one sentence.

    Args:
        words: The folded words of one candidate name.
        segments: The folded sentences of an opening paragraph.

    Returns:
        One span per occurrence, empty when the name is never stated.
    """
    width = len(words)
    return tuple(
        (index, start, start + width)
        for index, segment in enumerate(segments)
        for start in range(len(segment) - width + 1)
        if segment[start : start + width] == words
    )


def _shadowed(
    name: ConceptId,
    found: dict[ConceptId, tuple[Span, ...]],
    candidates: dict[ConceptId, Candidate],
) -> bool:
    """Test whether every statement of a name sits inside a longer one.

    `Lenten Espagnole` contains the word `espagnole`, and reading both as
    statements would turn one claim into a false ambiguity. A name shadows a
    shorter one only when the two reach different preparations, so a mother
    stated as `Béchamel Sauce` still records the mother.

    Args:
        name: The candidate name being tested.
        found: Every stated name and the spans it was stated at.
        candidates: Every name a stated parent may use.

    Returns:
        True if each of the name's spans lies inside a span of a longer
        name that reaches a different preparation.
    """
    width = len(name.split("-"))
    key = candidates[name].key
    covers = [
        span
        for other, spans in found.items()
        if len(other.split("-")) > width and candidates[other].key != key
        for span in spans
    ]
    return all(any(_inside(span, cover) for cover in covers) for span in found[name])


def _inside(span: Span, cover: Span) -> bool:
    """Test whether one span lies within another in the same sentence.

    Args:
        span: The span being tested.
        cover: The span that may contain it.

    Returns:
        True if `span` falls entirely within `cover`.
    """
    return span[0] == cover[0] and cover[1] <= span[1] and span[2] <= cover[2]


def _without_cycles(
    parents: dict[int, ConceptId | None], successor: dict[ConceptId, int]
) -> dict[int, ConceptId | None]:
    """Clear the parent of every preparation that lies on a cycle.

    A preparation is never its own ancestor. A cycle means the source stated
    contradictory derivations, so every link on the cycle is cleared rather
    than one of them chosen. Links leading into a cycle stay, and the chain
    beneath them now terminates.

    Args:
        parents: Resolved parent per entry number, `None` where unresolved.
        successor: Entry number each recorded concept resolves to.

    Returns:
        The same mapping, with every link on a cycle cleared.
    """
    cleared = dict(parents)
    for start in parents:
        trail: list[int] = []
        entry: int | None = start
        while entry is not None and entry not in trail:
            trail.append(entry)
            recorded = cleared.get(entry)
            entry = successor.get(recorded) if recorded is not None else None
        if entry is not None:
            for member in trail[trail.index(entry) :]:
                cleared[member] = None
    return cleared


def extract(source: SourceText) -> Catalogue:
    """Read every sauce preparation a source states.

    Args:
        source: The document to read.

    Returns:
        The catalogue of preparations found, with parents resolved where the
        source states them plainly. A parent may be any preparation in the
        catalogue, so resolution runs after every entry has been read.

    Raises:
        NoPreparationsFound: If the source yields no numbered entries at all,
            or yields entries of which none is a sauce. Either means the
            patterns in this module do not fit this source.
    """
    lines = source.lines()
    mothers = find_mothers("\n".join(lines))
    spans = sauce_chapters(lines)
    entries = list(iter_entries(lines))
    if not entries:
        msg = f"no numbered entries in {source.source_id}"
        raise NoPreparationsFound(msg)

    drafts = tuple(
        _preparation(source, entry)
        for entry in entries
        if is_sauce(entry[2], mothers, _within(entry[1], spans))
    )
    if not drafts:
        msg = f"{len(entries)} entries in {source.source_id}, none of them a sauce"
        raise NoPreparationsFound(msg)
    provisional = Catalogue(
        source_id=source.source_id, preparations=drafts, mothers=mothers
    )
    return Catalogue(
        source_id=source.source_id,
        preparations=_derived(provisional),
        mothers=mothers,
    )


def _derived(catalogue: Catalogue) -> tuple[Preparation, ...]:
    """Resolve every stated parent across a catalogue of drafts.

    Resolution needs the whole catalogue, because a parent may be any
    preparation in it. So the drafts are read first, and every parent is
    resolved against them in a second pass.

    Args:
        catalogue: The catalogue with every parent still unresolved.

    Returns:
        The same preparations, with each parent resolved where its opening
        paragraph states exactly one candidate, and no cycle recorded.
    """
    candidates = parent_candidates(catalogue)
    successor = {
        candidate.records: candidate.key
        for candidate in candidates.values()
        if isinstance(candidate.key, int)
    }
    parents = {
        draft.ref.entry: resolve_parent(draft.body, _own(draft), candidates)
        for draft in catalogue.preparations
    }
    parents = _without_cycles(parents, successor)
    return tuple(
        replace(draft, parent=parents[draft.ref.entry])
        for draft in catalogue.preparations
    )


def _own(draft: Preparation) -> frozenset[int | ConceptId]:
    """Collect the keys and names that denote a preparation itself.

    Args:
        draft: The preparation being resolved.

    Returns:
        The entry number, every term concept, and the folded title.
    """
    names: frozenset[int | ConceptId] = frozenset(term.concept for term in draft.terms)
    return names | {draft.ref.entry, to_concept_id(draft.title)}


def _within(index: int, spans: tuple[tuple[int, int], ...]) -> bool:
    """Test whether a line index falls inside any span.

    Args:
        index: The line index to place.
        spans: Half-open spans of line indices.

    Returns:
        True if the index falls inside one of the spans.
    """
    return any(start <= index < end for start, end in spans)


def _preparation(source: SourceText, entry: tuple[int, int, str, str]) -> Preparation:
    """Build one preparation from a numbered entry, its parent unresolved.

    Args:
        source: The document the entry came from.
        entry: Entry number, heading line index, title, and body prose.

    Returns:
        The preparation. Its parent is resolved later, against the whole
        catalogue.
    """
    number, index, title, body = entry
    return Preparation(
        title=title,
        terms=terms_in(title),
        body=body,
        ref=SourceRef(
            source_id=source.source_id,
            entry=number,
            line=source.line_offset + index + 1,
        ),
        parent=None,
    )
