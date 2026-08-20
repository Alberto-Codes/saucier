"""Value objects and type aliases for the domain.

Culinary terms are a controlled vocabulary. A term is never translated, so
every surface form carries the language it was written in, and equivalent
surface forms across languages resolve to one language-independent concept
identifier.

Examples:
    Fold two spellings of one term onto a single concept:

    ```python
    from saucier.domain.types import to_concept_id

    assert to_concept_id("Velouté") == to_concept_id("VELOUTE")
    ```

See Also:
    - [saucier.domain.models][]: The entities built from these values.
"""

from __future__ import annotations

import re
import unicodedata
from enum import StrEnum
from typing import NewType

ConceptId = NewType("ConceptId", str)
"""Language-independent identifier for one culinary concept.

`espagnole` and `salsa espanola` denote one concept and share one id. A
concept with no equivalent in another language simply has no label in it.
"""


class Language(StrEnum):
    """ISO 639-1 codes for languages the corpus is written in.

    Restricted to the languages actually present in tracked sources. Add a
    member when a source in that language is added, not in anticipation.

    Examples:
        Members carry their ISO code as the value:

        ```python
        assert Language.FRENCH == "fr"
        ```
    """

    ENGLISH = "en"
    FRENCH = "fr"
    SPANISH = "es"


def to_concept_id(surface: str) -> ConceptId:
    """Fold a surface form into a language-independent concept identifier.

    Strips diacritics and punctuation and lowercases, so that `Velouté` and
    `veloute` reach the same id. This is deliberately crude: it resolves
    orthographic variation only, never semantic equivalence across languages.
    Cross-language resolution is a later concern and needs evidence, not
    string folding.

    Args:
        surface: A term as it appears in a source, in any language.

    Returns:
        The concept identifier for that surface form.

    Raises:
        ValueError: If the surface form folds to an empty identifier.
    """
    decomposed = unicodedata.normalize("NFKD", surface.casefold())
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    folded = re.sub(r"[^a-z0-9]+", "-", stripped).strip("-")
    if not folded:
        msg = f"surface form yields an empty concept id: {surface!r}"
        raise ValueError(msg)
    return ConceptId(folded)
