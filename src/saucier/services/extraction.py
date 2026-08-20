"""Deterministic extraction of preparations from a numbered source.

No model runs here. Everything this module produces is traceable to a line
in the source, which is the point: it establishes how much structure the
source already carries, and therefore the bar any later model has to clear.

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

from saucier.domain.errors import NoPreparationsFound
from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
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


def resolve_parent(
    body: str, own: frozenset[ConceptId], mothers: frozenset[ConceptId]
) -> ConceptId | None:
    """Find the base preparation an entry's prose derives it from.

    Only the opening paragraph counts. Escoffier states an ingredient list
    first, so a base named there is being used; a base named eight paragraphs
    later is usually being compared against, not built on. A mother has to
    appear as a whole word, so `tomatoes` is not `tomato`.

    An entry naming none resolves to `None`. So does an entry naming two:
    `SHRIMP SAUCE` says "fish velouté or, failing this, Béchamel", and
    picking one of those is a guess the source did not make.

    Args:
        body: The entry's prose.
        own: Concepts the entry itself denotes, which cannot be its parent.
        mothers: Concepts the source names as base preparations.

    Returns:
        The parent concept, or None when the opening paragraph names no
        mother or names more than one.
    """
    opening = body.split("\n\n", 1)[0]
    if not opening.strip():
        return None
    words = set(to_concept_id(opening).split("-"))
    found = mothers.intersection(words) - own
    return next(iter(found)) if len(found) == 1 else None


def extract(source: SourceText) -> Catalogue:
    """Read every sauce preparation a source states.

    Args:
        source: The document to read.

    Returns:
        The catalogue of preparations found, with parents resolved where the
        source states them plainly.

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

    preparations = [
        _preparation(source, mothers, entry)
        for entry in entries
        if is_sauce(entry[2], mothers, _within(entry[1], spans))
    ]
    if not preparations:
        msg = f"{len(entries)} entries in {source.source_id}, none of them a sauce"
        raise NoPreparationsFound(msg)
    return Catalogue(
        source_id=source.source_id,
        preparations=tuple(preparations),
        mothers=mothers,
    )


def _within(index: int, spans: tuple[tuple[int, int], ...]) -> bool:
    """Test whether a line index falls inside any span.

    Args:
        index: The line index to place.
        spans: Half-open spans of line indices.

    Returns:
        True if the index falls inside one of the spans.
    """
    return any(start <= index < end for start, end in spans)


def _preparation(
    source: SourceText, mothers: frozenset[ConceptId], entry: tuple[int, int, str, str]
) -> Preparation:
    """Build one preparation from a numbered entry.

    Args:
        source: The document the entry came from.
        mothers: Concepts the source names as base preparations.
        entry: Entry number, heading line index, title, and body prose.

    Returns:
        The preparation, with its parent resolved where the prose states one.
    """
    number, index, title, body = entry
    terms = terms_in(title)
    own = frozenset(t.concept for t in terms) | {to_concept_id(title)}
    return Preparation(
        title=title,
        terms=terms,
        body=body,
        ref=SourceRef(
            source_id=source.source_id,
            entry=number,
            line=source.line_offset + index + 1,
        ),
        parent=resolve_parent(body, own, mothers),
    )
