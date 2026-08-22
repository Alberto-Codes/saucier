"""Compare two catalogues and say what caused each difference.

Crude on purpose, per ADR-0001 decision 0. The comparison does not have to
be right about everything. It has to be honest about which rows it is unsure
of, and an OCR witness guarantees there will be many.

Every row carries a cause rather than a bare delta. The naive comparison of
the two Escoffier witnesses reports fifteen removals, and a scanner explains
all fifteen. Reporting them as removals asserts a cause nobody established,
and that is the failure this module exists to avoid.

No row is adjudicated. A parent disagreement is reported with both readings
side by side, and the comparison never decides which witness is right.

Examples:
    Compare two stored catalogues:

    ```python
    from saucier.services.comparison import compare

    report = compare(
        older=store.load("escoffier-1907"), newer=store.load("escoffier-1909")
    )
    print(report.tally())
    ```

See Also:
    - [saucier.domain.witness][]: Where fidelity comes from.
    - [saucier.adapters.driving.cli][]: What renders a report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import StrEnum

from saucier.domain.models import Catalogue, Preparation
from saucier.domain.types import ConceptId
from saucier.domain.witness import Fidelity

RESEMBLANCE = 0.75
"""How alike two names must be before one may be read as a scan of the other.

Measured against the corpus rather than chosen. The fourteen known character
corruptions score 0.778 and above, and the highest scoring pair below this
line is unrelated. Every pair is reported with its score, so a reader can
disagree with the line.
"""


class Cause(StrEnum):
    """Why two catalogues differ on one concept.

    A row carries one or more. `OCR_SUSPECTED` can stand alone, when a name
    in one witness reads as a scan of a name in the other, and it can qualify
    another cause, when an OCR witness makes a parent disagreement
    unattributable. `RETITLED` needs two proofread witnesses, because a scan
    that drops the end of a heading looks exactly like a heading that grew.

    Examples:
        Members carry their printed value:

        ```python
        assert Cause.OCR_SUSPECTED == "ocr-suspected"
        ```
    """

    ADDED = "added"
    REMOVED = "removed"
    RETITLED = "retitled"
    PARENT_CHANGED = "parent-changed"
    OCR_SUSPECTED = "ocr-suspected"


@dataclass(frozen=True, slots=True, kw_only=True)
class Difference:
    """One row: a concept, what each witness holds, and the cause.

    Attributes:
        causes (tuple[Cause, ...]): Why the two witnesses differ here.
        concept (ConceptId): The concept this row is about.
        counterpart (ConceptId | None): The concept it pairs with in the
            other witness, when the two names are not identical.
        older (str | None): What the older witness records.
        newer (str | None): What the newer witness records.
        note (str): The evidence for the cause, in a reader's words.

    Examples:
        A row states its cause rather than a bare delta:

        ```python
        print(row.causes, row.concept, row.note)
        ```
    """

    causes: tuple[Cause, ...]
    concept: ConceptId
    counterpart: ConceptId | None = None
    older: str | None = None
    newer: str | None = None
    note: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class Report:
    """What two catalogues say about each other.

    Attributes:
        older (str): Source id of the earlier witness.
        newer (str): Source id of the later witness.
        scanned (bool): Whether either witness is OCR, which is what makes a
            difference unattributable.
        presence (tuple[Difference, ...]): Concepts one witness holds and the
            other does not.
        parents (tuple[Difference, ...]): Shared concepts whose recorded
            parent disagrees.

    Examples:
        Count the rows by cause:

        ```python
        assert report.tally()[Cause.ADDED] >= 0
        ```
    """

    older: str
    newer: str
    scanned: bool
    presence: tuple[Difference, ...] = field(default_factory=tuple)
    parents: tuple[Difference, ...] = field(default_factory=tuple)

    def tally(self) -> dict[Cause, int]:
        """Count how many rows carry each cause.

        A row carrying two causes counts once under each, so the totals do
        not sum to the row count.

        Returns:
            One count per cause that appears, in declaration order.
        """
        rows = (*self.presence, *self.parents)
        return {
            cause: sum(1 for row in rows if cause in row.causes)
            for cause in Cause
            if any(cause in row.causes for row in rows)
        }


def _index(catalogue: Catalogue) -> dict[ConceptId, Preparation]:
    """Index a catalogue by the concept each preparation is filed under.

    Args:
        catalogue: The catalogue to index.

    Returns:
        One preparation per concept, first occurrence winning.
    """
    index: dict[ConceptId, Preparation] = {}
    for preparation in catalogue.preparations:
        index.setdefault(preparation.concept, preparation)
    return index


def _keeps_words_of(one: ConceptId, other: ConceptId) -> bool:
    """Test whether one name is the other plus whole words.

    One heading keeps the other and adds to it. So the shorter name has to
    appear as a contiguous run of whole words inside the longer one, and it
    has to be at least half of it. A one-word run inside a five-word name is
    a coincidence rather than a heading that grew.

    Args:
        one: One unshared concept.
        other: The other unshared concept.

    Returns:
        True if the shorter name is most of the longer one, whole words.
    """
    first, second = sorted((one.split("-"), other.split("-")), key=len)
    span = len(first)
    if span < 2 or span * 2 < len(second):  # noqa: PLR2004
        return False
    return any(second[i : i + span] == first for i in range(len(second) - span + 1))


def _resembles(older: ConceptId, newer: ConceptId) -> float:
    """Score how alike two concept ids are, character by character.

    Args:
        older: A concept only the earlier witness holds.
        newer: A concept only the later witness holds.

    Returns:
        A ratio from 0 to 1.
    """
    return SequenceMatcher(None, older, newer).ratio()


Pairing = dict[ConceptId, tuple[ConceptId, Cause, str]]
"""Each paired older concept, its counterpart, the cause, and the evidence."""

Candidate = tuple[float, ConceptId, ConceptId, Cause, str]
"""A pair a stated cause can explain: score, both names, the cause, the why."""

INSIDE_WORDS = "the two names differ inside words"
WHOLE_WORDS = "one heading is the other plus whole words"
SCANNED = "a witness is ocr, so this may be the scanner"


def _candidates(
    older: list[ConceptId], newer: list[ConceptId], scanned: bool
) -> list[Candidate]:
    """Collect every unshared pair some stated cause can explain.

    Two hypotheses, and which one applies depends on the witnesses. A heading
    that gained whole words, between two proofread texts, is a retitle. With
    a scanned witness it is not, because a scan breaks a heading across a
    line and loses the rest of it. `BEARNAISE SAUCE WITH MEAT GLAZE` reads as
    a retitle by that test, and the two books print the same heading.

    A name differing inside its words is only ever read as a scan artefact,
    because two proofread texts do not disagree one character at a time.

    Args:
        older: Concepts only the earlier witness holds.
        newer: Concepts only the later witness holds.
        scanned: Whether either witness is OCR.

    Returns:
        Every candidate pair, each carrying the cause it would be read as.
    """
    found: list[Candidate] = []
    for one in older:
        for two in newer:
            score = _resembles(one, two)
            if _keeps_words_of(one, two):
                cause = Cause.OCR_SUSPECTED if scanned else Cause.RETITLED
                why = f"{WHOLE_WORDS}, and {SCANNED}" if scanned else WHOLE_WORDS
                found.append((score, one, two, cause, why))
            elif scanned and score >= RESEMBLANCE:
                found.append(
                    (
                        score,
                        one,
                        two,
                        Cause.OCR_SUSPECTED,
                        f"{INSIDE_WORDS}, and {SCANNED}",
                    )
                )
    return found


def _pair(older: list[ConceptId], newer: list[ConceptId], scanned: bool) -> Pairing:
    """Match each unshared concept to a counterpart, and say why.

    Greedy and one to one, best score first, ties broken by concept id so the
    result never depends on dictionary order.

    Args:
        older: Concepts only the earlier witness holds.
        newer: Concepts only the later witness holds.
        scanned: Whether either witness is OCR.

    Returns:
        Every pair found, keyed by the older concept.
    """
    paired: Pairing = {}
    taken: set[ConceptId] = set()
    ranked = sorted(_candidates(older, newer, scanned), key=lambda c: (-c[0], c[1]))
    for score, one, two, cause, why in ranked:
        if one in paired or two in taken:
            continue
        paired[one] = (two, cause, f"{why}, at {score:.2f}")
        taken.add(two)
    return paired


def _presence(
    older: dict[ConceptId, Preparation],
    newer: dict[ConceptId, Preparation],
    scanned: bool,
) -> tuple[Difference, ...]:
    """Report every concept one witness holds and the other does not.

    Args:
        older: The earlier witness, indexed by concept.
        newer: The later witness, indexed by concept.
        scanned: Whether either witness is OCR.

    Returns:
        Rows in concept order, paired names reported once.
    """
    only_older = sorted(set(older) - set(newer))
    only_newer = sorted(set(newer) - set(older))
    paired = _pair(only_older, only_newer, scanned)
    matched = {counterpart for counterpart, _, _ in paired.values()}
    unresembled = "no name in the other witness resembles it"
    rows = [
        Difference(
            causes=(paired[c][1],),
            concept=c,
            counterpart=paired[c][0],
            older=older[c].title,
            newer=newer[paired[c][0]].title,
            note=paired[c][2],
        )
        if c in paired
        else Difference(
            causes=(Cause.REMOVED,),
            concept=c,
            older=older[c].title,
            note=unresembled,
        )
        for c in only_older
    ]
    rows.extend(
        Difference(
            causes=(Cause.ADDED,),
            concept=c,
            newer=newer[c].title,
            note=unresembled,
        )
        for c in only_newer
        if c not in matched
    )
    return tuple(sorted(rows, key=lambda row: (row.causes[0].value, row.concept)))


def _parents(
    older: dict[ConceptId, Preparation],
    newer: dict[ConceptId, Preparation],
    scanned: bool,
) -> tuple[Difference, ...]:
    """Report every shared concept whose recorded parent disagrees.

    Nothing is adjudicated here. With an OCR witness in the comparison, a
    lost candidate explains a disagreement as well as a revision does, and
    telling them apart needs both source lines read by eye.

    Args:
        older: The earlier witness, indexed by concept.
        newer: The later witness, indexed by concept.
        scanned: Whether either witness is OCR.

    Returns:
        Rows in concept order.
    """
    causes = (
        (Cause.PARENT_CHANGED, Cause.OCR_SUSPECTED)
        if scanned
        else (Cause.PARENT_CHANGED,)
    )
    note = (
        "one witness is ocr, so a lost candidate explains this as well as a revision"
        if scanned
        else "both witnesses are proofread"
    )
    return tuple(
        Difference(
            causes=causes,
            concept=concept,
            older=older[concept].parent,
            newer=newer[concept].parent,
            note=note,
        )
        for concept in sorted(set(older) & set(newer))
        if older[concept].parent != newer[concept].parent
    )


def compare(older: Catalogue, newer: Catalogue) -> Report:
    """Compare two catalogues of one work.

    Args:
        older: The earlier witness.
        newer: The later witness.

    Returns:
        Every difference found, each row carrying the cause it was read as.
    """
    scanned = Fidelity.OCR in {older.fidelity, newer.fidelity}
    indexed = (_index(older), _index(newer))
    return Report(
        older=older.source_id,
        newer=newer.source_id,
        scanned=scanned,
        presence=_presence(*indexed, scanned),
        parents=_parents(*indexed, scanned),
    )
