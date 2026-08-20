"""Deterministic extraction of preparations from a numbered source.

No model runs here. Everything this module produces is traceable to a line
in the source, which is the point: it establishes how much structure the
source already carries, and therefore the bar any later model has to clear.

Examples:
    Read a catalogue and report what stayed unresolved:

    ```python
    from saucier.services.extraction import extract

    catalogue = extract(source)
    unresolved = len(catalogue.preparations) - catalogue.resolved
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

DISH = re.compile(r"\bWITH\b|\bSAUCES\b", re.IGNORECASE)
"""`ASPARAGUS WITH VARIOUS SAUCES` is a dish that takes a sauce, not a sauce."""

ASCII_MAX = 127
"""Above this codepoint a character carries a diacritic the source kept."""

FRENCH_MARKERS = frozenset(
    {"espagnole", "veloute", "bechamel", "hollandaise", "roux", "glaze-de-viande"}
)
"""Terms known to be French even when written without diacritics."""


def _language_of(surface: str) -> Language:
    """Guess the language a term is written in.

    Uses three signals: non-ASCII letters, French noun-adjective word order
    (`SAUCE BIGARRADE` rather than `BIGARRADE SAUCE`), and a small lexicon of
    French terms that survive into English without their diacritics.

    Args:
        surface: The term as written.

    Returns:
        The language the term appears to be written in.
    """
    if any(ord(char) > ASCII_MAX for char in surface):
        return Language.FRENCH
    if surface.upper().startswith("SAUCE "):
        return Language.FRENCH
    if to_concept_id(surface) in FRENCH_MARKERS:
        return Language.FRENCH
    return Language.ENGLISH


def terms_in(title: str) -> tuple[Term, ...]:
    """Split an entry heading into its language-tagged alternative names.

    Args:
        title: The entry heading, verbatim.

    Returns:
        One term per alternative name in the heading, in heading order.
    """
    parts = (part.strip(" .—") for part in ALTERNATIVES.split(title))
    return tuple(Term.of(part, _language_of(part)) for part in parts if part)


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


def iter_entries(lines: list[str]) -> Iterator[tuple[int, int, str, str]]:
    """Walk the source, yielding one numbered entry at a time.

    Args:
        lines: The source body as lines.

    Yields:
        Tuples of entry number, line number, title, and body prose.
    """
    start: int | None = None
    number = 0
    title = ""
    for index, line in enumerate(lines):
        match = ENTRY.match(line)
        if not match:
            continue
        if start is not None:
            yield number, start + 1, title, "\n".join(lines[start + 1 : index]).strip()
        number, title, start = int(match.group(1)), match.group(2).strip(), index
    if start is not None:
        yield number, start + 1, title, "\n".join(lines[start + 1 :]).strip()


def is_sauce(title: str, mothers: frozenset[ConceptId]) -> bool:
    """Decide whether an entry is a sauce this catalogue should carry.

    An entry qualifies if its heading says "sauce", or if it names one of the
    base preparations — which catches derivatives such as `LENTEN ESPAGNOLE`
    that never use the word. Headings shaped like a dish are rejected:
    `ASPARAGUS WITH VARIOUS SAUCES` is something a sauce is served on.

    Args:
        title: The entry heading.
        mothers: Concepts the source names as base preparations.

    Returns:
        True if the entry belongs in a sauce catalogue.
    """
    if DISH.search(title):
        return False
    if "SAUCE" in title.upper():
        return True
    folded = to_concept_id(title)
    return any(mother in folded for mother in mothers)


def resolve_parent(
    body: str, own: frozenset[ConceptId], mothers: frozenset[ConceptId]
) -> ConceptId | None:
    """Find the base preparation an entry's prose derives it from.

    Only the opening paragraph counts. Escoffier states an ingredient list
    first, so a base named there is being used; a base named eight paragraphs
    later is usually being compared against, not built on. An entry naming
    none resolves to `None` rather than to a guess.

    Args:
        body: The entry's prose.
        own: Concepts the entry itself denotes, which cannot be its parent.
        mothers: Concepts the source names as base preparations.

    Returns:
        The parent concept, or None when the opening paragraph names none.
    """
    opening = body.split("\n\n", 1)[0]
    if not opening.strip():
        return None
    folded = to_concept_id(opening)
    found = [m for m in sorted(mothers) if m not in own and m in folded]
    return found[0] if found else None


def extract(source: SourceText) -> Catalogue:
    """Read every sauce preparation a source states.

    Args:
        source: The document to read.

    Returns:
        The catalogue of preparations found, with parents resolved where the
        source states them plainly.

    Raises:
        NoPreparationsFound: If the source yields no numbered entries at all,
            which means the entry pattern does not fit this source.
    """
    lines = source.lines()
    mothers = find_mothers("\n".join(lines))
    entries = list(iter_entries(lines))
    if not entries:
        msg = f"no numbered entries in {source.source_id}"
        raise NoPreparationsFound(msg)

    preparations = []
    for number, line_no, title, body in entries:
        if not is_sauce(title, mothers):
            continue
        terms = terms_in(title)
        own = frozenset(t.concept for t in terms) | {to_concept_id(title)}
        preparations.append(
            Preparation(
                title=title,
                terms=terms,
                body=body,
                ref=SourceRef(source.source_id, number, line_no),
                parent=resolve_parent(body, own, mothers),
            )
        )
    return Catalogue(
        source_id=source.source_id,
        preparations=tuple(preparations),
        mothers=mothers,
    )
