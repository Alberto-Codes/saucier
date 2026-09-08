"""What counts as a statement inside an entry's prose.

ADR-0008 narrowed a statement to a whole run of words inside one sentence of
the opening paragraph. That test decides two different questions, so it lives
here rather than beside either caller. Resolution asks which preparations an
opening states. A lookup asks whether a preparation states the base it is
being offered as, which is how a derivative is kept from standing in for its
own base.

Folding flattens punctuation, so the sentence boundary is drawn before the
fold. Without it a run could join words across a full stop, which is the
substring defect ADR-0007 records.

Examples:
    Read the runs an opening paragraph states:

    ```python
    from saucier.domain.statement import folded_segments, spans_in
    from saucier.domain.types import ConceptId

    segments = folded_segments("Boil one pint of Bechamel. Season it.")
    assert spans_in(ConceptId("bechamel").split("-"), segments)
    ```

See Also:
    - [saucier.domain.types][]: The fold every run is measured in.
    - [saucier.services.extraction][]: The resolver that reads the runs.
"""

from __future__ import annotations

import re

from saucier.domain.types import to_concept_id

SEGMENT = re.compile(r"[.!?;:]")
"""Sentence boundaries. A name split across two sentences is not a statement."""

WORDED = re.compile(r"[a-zA-Z0-9]")
"""A segment with no letter or digit folds to nothing and is skipped."""

Span = tuple[int, int, int]
"""Where a name was stated: segment index, first word, one past the last."""


def folded_segments(body: str) -> tuple[list[str], ...]:
    """Fold an entry's opening paragraph into sentence-bounded word runs.

    Args:
        body: The entry's prose, verbatim. Only the opening paragraph is
            read, because a base named eight paragraphs later is being
            compared against rather than built on.

    Returns:
        One list of folded words per sentence that carries any.
    """
    return tuple(
        to_concept_id(segment).split("-")
        for segment in SEGMENT.split(body.split("\n\n", 1)[0])
        if WORDED.search(segment)
    )


def spans_in(words: list[str], segments: tuple[list[str], ...]) -> tuple[Span, ...]:
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


def inside(span: Span, cover: Span) -> bool:
    """Test whether one span lies within another in the same sentence.

    Args:
        span: The span being tested.
        cover: The span that may contain it.

    Returns:
        True if `span` falls entirely within `cover`.
    """
    return span[0] == cover[0] and cover[1] <= span[1] and span[2] <= cover[2]
