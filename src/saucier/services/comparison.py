"""Compare two catalogues and say what caused each difference.

Crude on purpose, per ADR-0001 decision 0. The comparison does not have to
be right about everything. It has to be honest about which rows it is unsure
of, and an OCR witness guarantees there will be many.

Every row carries a cause rather than a bare delta. The naive comparison of
the two Escoffier witnesses reports fourteen removals, and a scanner explains
all fourteen. Reporting them as removals asserts a cause nobody established,
and that is the failure this module exists to avoid.

A cause is itself a claim and can itself be wrong. This module once blamed a
scanner for a heading its own reader had truncated, which is the same failure
one level up. A row that says nothing resembles it has to have looked, and a
derivation is compared for every preparation rather than only for the ones
both witnesses spell the same way.

No row is adjudicated. A parent disagreement is reported with both readings
side by side, and the comparison never decides which witness is right.

Nor is absence. A scanned witness has a measured blind spot, so a concept
found in one witness and not the other is reported as unmatched rather than
as added or removed. ADR-0014 records why, and the summary prints the blind
spot beside the counts.

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
corruptions score 0.778 and above. The margin below is thin: an unrelated
pair scores 0.756, and it stays out because both its names pair better with
something else rather than because of this number. Every row prints its
score, so a reader can disagree with the line.
"""


class Cause(StrEnum):
    """Why two catalogues differ on one concept.

    A row carries one or more. `OCR_SUSPECTED` can stand alone, when a name
    in one witness reads as a scan of a name in the other. It can also
    qualify another cause, when a scanned witness leaves a row
    unattributable, and it decides nothing when it does.

    `ADDED` and `REMOVED` state what a book contains, so they are available
    only between two witnesses of equal fidelity. Against a scanned witness
    the same row is `UNMATCHED`, which states what the comparison found and
    nothing about the book. ADR-0014 records why.

    Examples:
        Members carry their printed value:

        ```python
        assert Cause.OCR_SUSPECTED == "ocr-suspected"
        ```
    """

    ADDED = "added"
    REMOVED = "removed"
    UNMATCHED = "unmatched"
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
        entries_read (tuple[int | None, int | None]): Numbered entries each
            witness yielded. The gap between them is the blind spot, and it
            is what an unmatched row cannot see past.
        presence (tuple[Difference, ...]): Concepts one witness holds and the
            other does not.
        parents (tuple[Difference, ...]): Shared concepts whose recorded
            parent disagrees.

    Examples:
        Count the rows by cause:

        ```python
        assert report.tally()[Cause.UNMATCHED] >= 0
        ```
    """

    older: str
    newer: str
    scanned: bool
    entries_read: tuple[int | None, int | None] = (None, None)
    presence: tuple[Difference, ...] = field(default_factory=tuple)
    parents: tuple[Difference, ...] = field(default_factory=tuple)

    @property
    def blind_spot(self) -> int | None:
        """Entries one witness yielded and the other did not.

        Returns:
            The gap between the two entry counts, or None when either
            catalogue recorded no count.
        """
        older, newer = self.entries_read
        if older is None or newer is None:
            return None
        return abs(newer - older)

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


Pairing = dict[ConceptId, tuple[ConceptId, tuple[Cause, ...], str]]
"""Each paired older concept, its counterpart, the causes, and the evidence."""

Candidate = tuple[float, ConceptId, ConceptId, tuple[Cause, ...], str]
"""A pair a stated cause can explain: score, both names, the causes, the why."""

INSIDE_WORDS = "the two names differ inside words"
WHOLE_WORDS = "one heading is the other plus whole words"
SCANNED = "a witness is ocr, so the diff cannot say which"


def _candidates(
    older: list[ConceptId], newer: list[ConceptId], scanned: bool
) -> list[Candidate]:
    """Collect every unshared pair some stated cause can explain.

    Two hypotheses, tested by different evidence. A heading that gained whole
    words is a retitle, because a scanner damages characters rather than
    inventing coherent words. A name differing inside its words is a scan
    artefact, because two proofread texts do not disagree one character at a
    time.

    A scanned witness does not overturn the first reading, and it does not
    confirm it either. A scan can drop a heading's tail at a page break, so
    the row carries both causes and decides nothing.

    Args:
        older: Concepts only the earlier witness holds.
        newer: Concepts only the later witness holds.
        scanned: Whether either witness is OCR.

    Returns:
        Every candidate pair, each carrying the causes it would be read as.
    """
    found: list[Candidate] = []
    for one in older:
        for two in newer:
            score = _resembles(one, two)
            if _keeps_words_of(one, two):
                causes = (
                    (Cause.RETITLED, Cause.OCR_SUSPECTED)
                    if scanned
                    else (Cause.RETITLED,)
                )
                why = f"{WHOLE_WORDS}, and {SCANNED}" if scanned else WHOLE_WORDS
                found.append((score, one, two, causes, why))
            elif scanned and score >= RESEMBLANCE:
                found.append(
                    (
                        score,
                        one,
                        two,
                        (Cause.OCR_SUSPECTED,),
                        f"{INSIDE_WORDS}, and {SCANNED}",
                    )
                )
    return found


def _pair(older: list[ConceptId], newer: list[ConceptId], scanned: bool) -> Pairing:
    """Match each unshared concept to a counterpart, and say why.

    Greedy and one to one, best score first, ties broken by concept id so the
    result never depends on dictionary order. A name reaching two candidates
    goes to the better one, which is what keeps the pair at 0.756 out.

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
    for score, one, two, causes, why in ranked:
        if one in paired or two in taken:
            continue
        paired[one] = (two, causes, f"{why}, at {score:.2f}")
        taken.add(two)
    return paired


def _unpaired_note(concept: ConceptId, others: list[ConceptId], scanned: bool) -> str:
    """Say what was actually looked for, and what was found.

    A row that claims nothing resembles it has to have looked. Between two
    proofread witnesses nothing is looked for at all, and a name that lost a
    greedy contest does have a resemblance worth printing.

    Args:
        concept: The unshared concept this row is about.
        others: Every concept only the other witness holds.
        scanned: Whether either witness is OCR.

    Returns:
        The evidence for reading this row as an addition or a removal.
    """
    if not scanned:
        return "no witness is ocr, so no name was tested against it"
    scored = [(_resembles(concept, other), other) for other in others]
    if not scored:
        return "the other witness holds no unshared name"
    score, closest = max(scored)
    if score < RESEMBLANCE:
        return f"the closest unshared name is {closest}, at {score:.2f}"
    return f"{closest} resembles it at {score:.2f}, and pairs better elsewhere"


def _unshared_causes(scanned: bool) -> tuple[Cause, Cause]:
    """Choose what a concept held by one witness alone may be called.

    A scanned witness has a measured blind spot, so the diff knows it did not
    find a counterpart and does not know the book lacks one. Between two
    proofread texts there is no such gap, and the stronger reading stands.

    Args:
        scanned: Whether either witness is OCR.

    Returns:
        The cause for a concept only the earlier witness holds, and the cause
        for one only the later witness holds.
    """
    if scanned:
        return Cause.UNMATCHED, Cause.UNMATCHED
    return Cause.REMOVED, Cause.ADDED


def _presence(
    older: dict[ConceptId, Preparation],
    newer: dict[ConceptId, Preparation],
    paired: Pairing,
    scanned: bool,
) -> tuple[Difference, ...]:
    """Report every concept one witness holds and the other does not.

    Args:
        older: The earlier witness, indexed by concept.
        newer: The later witness, indexed by concept.
        paired: Unshared names matched across the two witnesses.
        scanned: Whether either witness is OCR.

    Returns:
        Rows in concept order. A paired name is one row, not two, so an
        attributed pair leaves the unshared counts alone.
    """
    only_older = sorted(set(older) - set(newer))
    only_newer = sorted(set(newer) - set(older))
    matched = {counterpart for counterpart, _, _ in paired.values()}
    gone, arrived = _unshared_causes(scanned)
    rows = [
        Difference(
            causes=paired[c][1],
            concept=c,
            counterpart=paired[c][0],
            older=older[c].title,
            newer=newer[paired[c][0]].title,
            note=paired[c][2],
        )
        if c in paired
        else Difference(
            causes=(gone,),
            concept=c,
            older=older[c].title,
            note=_unpaired_note(c, only_newer, scanned),
        )
        for c in only_older
    ]
    rows.extend(
        Difference(
            causes=(arrived,),
            concept=c,
            newer=newer[c].title,
            note=_unpaired_note(c, only_older, scanned),
        )
        for c in only_newer
        if c not in matched
    )
    return tuple(sorted(rows, key=lambda row: (row.causes[0].value, row.concept)))


def _one_preparation(
    older: ConceptId | None, newer: ConceptId | None, paired: Pairing
) -> bool:
    """Test whether two recorded parents reach the same preparation.

    A parent named under a scanned spelling in one witness and a clean one in
    the other is one derivation, not two. Reading it as a change would let
    this module's own pairing manufacture a finding.

    Args:
        older: What the earlier witness recorded, or None.
        newer: What the later witness recorded, or None.
        paired: Unshared names matched across the two witnesses.

    Returns:
        True if both witnesses recorded the same derivation.
    """
    if older == newer:
        return True
    if older is None or newer is None:
        return False
    return paired.get(older, (None,))[0] == newer


def _parents(
    older: dict[ConceptId, Preparation],
    newer: dict[ConceptId, Preparation],
    paired: Pairing,
    scanned: bool,
) -> tuple[Difference, ...]:
    """Report every preparation whose recorded parent disagrees.

    A preparation reaches this comparison two ways. It carries the same
    concept in both witnesses, or its two names were paired above. Comparing
    only the first would drop the derivations of every scanned name, which is
    a third of them on the committed corpus.

    Nothing is adjudicated here. With an OCR witness in the comparison, a
    lost candidate explains a disagreement as well as a revision does, and
    telling them apart needs both source lines read by eye.

    Args:
        older: The earlier witness, indexed by concept.
        newer: The later witness, indexed by concept.
        paired: Unshared names matched across the two witnesses.
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
    couples = [(concept, concept) for concept in set(older) & set(newer)]
    couples += [(one, two) for one, (two, _, _) in paired.items()]
    return tuple(
        Difference(
            causes=causes,
            concept=one,
            counterpart=None if one == two else two,
            older=older[one].parent,
            newer=newer[two].parent,
            note=note,
        )
        for one, two in sorted(couples)
        if not _one_preparation(older[one].parent, newer[two].parent, paired)
    )


def compare(older: Catalogue, newer: Catalogue) -> Report:
    """Compare two catalogues of one work.

    Names are paired once, and both sections read that pairing. So a scanned
    name reported in `names` has its derivation compared in `parents` too,
    under the same two ids. The entry counts travel with the report, because
    what a witness did not yield bounds what the report may claim.

    Args:
        older: The earlier witness.
        newer: The later witness.

    Returns:
        Every difference found, each row carrying the cause it was read as.
    """
    scanned = Fidelity.OCR in {older.fidelity, newer.fidelity}
    a, b = _index(older), _index(newer)
    paired = _pair(sorted(set(a) - set(b)), sorted(set(b) - set(a)), scanned)
    return Report(
        older=older.source_id,
        newer=newer.source_id,
        scanned=scanned,
        entries_read=(older.entries_read, newer.entries_read),
        presence=_presence(a, b, paired, scanned),
        parents=_parents(a, b, paired, scanned),
    )
