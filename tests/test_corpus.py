"""Tests against the committed Escoffier texts.

These lock in what each source actually says, so a parser change that quietly
loses preparations, or quietly gains some, fails here rather than in a blog
post.

The published counts live in `conftest.REVISION` and
`conftest.FIRST_PRINTING`. Changing them is a deliberate act: update the
README, the tutorial, and the documentation home page in the same commit, and
say why in the changelog.

The `escoffier` fixture is the 1909 revision, whose census two published
posts quote. The `escoffier_1907` fixture is the scanned first printing.
"""

import re
from fractions import Fraction

import pytest

from saucier.adapters.driven.hand_procedures import HandProcedures
from saucier.adapters.driven.normalised import normalise, repair_separator
from saucier.domain.types import ConceptId
from saucier.domain.witness import Fidelity
from saucier.infrastructure.bootstrap import escoffier_sources
from saucier.infrastructure.config import Paths
from saucier.services.extraction import (
    ENTRY,
    continues_heading,
    extract,
    own_names,
    parent_candidates,
    stated_candidates,
)
from saucier.services.procedure import procedure_of


@pytest.mark.corpus
def test_the_source_names_its_own_five_base_sauces(escoffier):
    assert escoffier.mothers == frozenset(
        {"espagnole", "veloute", "bechamel", "tomato", "hollandaise"}
    )


@pytest.mark.corpus
def test_the_published_census_still_holds(escoffier, census):
    assert len(escoffier.preparations) == census.sauces
    assert escoffier.resolved == census.derived
    assert escoffier.unresolved == census.unresolved


@pytest.mark.corpus
def test_espagnole_states_brown_roux_and_is_never_its_own_child(escoffier):
    """Entry 22 opens with "One lb. of brown roux". A mother is not a root."""
    espagnole = escoffier.find(ConceptId("espagnole"))
    assert espagnole is not None
    assert espagnole.parent == "brown-roux"
    assert espagnole not in escoffier.children_of(ConceptId("espagnole"))


@pytest.mark.corpus
def test_every_mother_the_parser_prints_can_be_looked_up(escoffier):
    for mother in escoffier.mothers:
        found = escoffier.find(mother)
        assert found is not None, f"{mother} is advertised but unreachable"


@pytest.mark.corpus
def test_french_terms_survive_untranslated(escoffier):
    bordelaise = escoffier.find(ConceptId("bordelaise"))
    assert bordelaise is not None
    assert bordelaise.title == "SAUCE BORDELAISE"


@pytest.mark.corpus
def test_every_line_reference_lands_on_its_own_heading(escoffier):
    """The provenance claim, checked the way a reader would check it."""
    path = Paths.discover().escoffier_transcription
    lines = path.read_text(encoding="utf-8").splitlines()
    for preparation in escoffier.preparations:
        found = lines[preparation.ref.line - 1]
        assert found.startswith(f"{preparation.ref.entry}—"), (
            f"entry {preparation.ref.entry} claims line {preparation.ref.line}, "
            f"which reads {found!r}"
        )


@pytest.mark.corpus
def test_no_dish_entries_leaked_into_the_sauce_catalogue(escoffier):
    """Headings a reader can confirm are not sauces, by name."""
    known_dishes = {
        "BOMBE HOLLANDAISE",
        "TOMATO SALAD",
        "GRILLED TOMATOES",
        "TOMATO JAM",
        "SOLE A LA HOLLANDAISE",
        "THE VELOUTÉS",
        "VELOUTÉ AGNÈS SOREL",
        "ASPARAGUS WITH VARIOUS SAUCES",
    }
    titles = {p.title for p in escoffier.preparations}
    assert not titles & known_dishes


@pytest.mark.corpus
def test_sauces_served_with_something_are_still_sauces(escoffier):
    titles = {p.title for p in escoffier.preparations}
    assert "SOUBISE SAUCE WITH RICE" in titles
    assert "EGG SAUCE WITH MELTED BUTTER" in titles


@pytest.mark.corpus
def test_a_recorded_parent_is_always_an_exact_catalogued_name(escoffier):
    """Exact membership, not a fuzzy lookup, so a fragment cannot pass."""
    names = escoffier.by_concept()
    for preparation in escoffier.preparations:
        if preparation.parent is not None:
            assert (
                preparation.parent in names or preparation.parent in escoffier.mothers
            )


@pytest.mark.corpus
def test_the_veloute_mother_binds_to_its_own_entry(escoffier):
    """Entry 25, not the Allemande whose alias is THICKENED VELOUTÉ."""
    veloute = escoffier.find(ConceptId("veloute"))
    assert veloute is not None
    assert veloute.title == "ORDINARY VELOUTÉ SAUCE"
    assert veloute.ref.entry == 25


@pytest.mark.corpus
def test_stating_two_preparations_of_one_family_stays_unresolved(escoffier):
    """Entry 73 says "substituting Allemande Sauce for the velouté"."""
    chaud_froid = escoffier.find(ConceptId("ordinary-chaud-froid-sauce"))
    assert chaud_froid is not None
    assert chaud_froid.parent is None


@pytest.mark.corpus
def test_marrow_sauce_resolves_to_bordelaise(escoffier):
    """Entry 45 says "only a variety of the Bordelaise", at line 1895."""
    marrow = escoffier.find(ConceptId("marrow-sauce"))
    assert marrow is not None
    assert marrow.parent == "sauce-bordelaise"
    children = escoffier.children_of(ConceptId("bordelaise"))
    assert marrow in children


@pytest.mark.corpus
def test_bordelaise_resolves_to_half_glaze(escoffier):
    """Entry 32 says "add one-half pint of half-glaze", at line 1685.

    Half glaze is entry 23, inside THE LEADING WARM SAUCES, and it enters on
    the chapter. Before ADR-0015 the mother clause kept it out, and this
    sauce stayed unresolved with its base on the page.
    """
    bordelaise = escoffier.find(ConceptId("bordelaise"))
    assert bordelaise is not None
    assert bordelaise.title == "SAUCE BORDELAISE"
    assert bordelaise.parent == "half-glaze"


@pytest.mark.corpus
def test_the_chain_above_robert_is_the_one_the_book_wrote(escoffier):
    """Robert to half glaze to Espagnole to brown roux, then nothing.

    Lines 1999, 1439, and 1394 of the 1909 text state the three links.
    """
    robert = escoffier.find(ConceptId("robert-sauce"))
    half_glaze = escoffier.find(ConceptId("half-glaze"))
    espagnole = escoffier.find(ConceptId("espagnole"))
    brown_roux = escoffier.find(ConceptId("brown-roux"))
    assert robert is not None and half_glaze is not None
    assert espagnole is not None and brown_roux is not None
    assert robert.parent == "half-glaze"
    assert half_glaze.parent == "espagnole"
    assert half_glaze.ref.entry == 23
    assert espagnole.parent == "brown-roux"
    assert brown_roux.parent is None


@pytest.mark.corpus
def test_the_roux_chain_terminates_at_brown_roux(escoffier):
    """Pale roux states brown roux, white roux states pale roux. No cycle."""
    pale = escoffier.find(ConceptId("pale-roux"))
    white = escoffier.find(ConceptId("white-roux"))
    assert pale is not None and white is not None
    assert pale.parent == "brown-roux"
    assert white.parent == "pale-roux"


@pytest.mark.corpus
def test_a_mother_with_a_parent_still_binds_to_its_own_entry(escoffier):
    """Espagnole and Velouté now state a roux. They are still the mothers."""
    assert escoffier.find(ConceptId("espagnole")).ref.entry == 22
    assert escoffier.find(ConceptId("veloute")).ref.entry == 25
    assert escoffier.find(ConceptId("veloute")).parent == "pale-roux"


@pytest.mark.corpus
def test_cardinal_states_two_candidates_and_stays_unresolved(escoffier):
    """Entry 69, line 2194, states Béchamel and then lobster butter.

    "Boil one pint of Béchamel" and then "finish the sauce ... with three
    oz. of very red lobster butter (No. 149)". The source stated one base
    and one finish. The resolver reads names and
    cannot tell them apart, so it refuses. ADR-0012 says that is right.
    """
    cardinal = escoffier.find(ConceptId("cardinal-sauce"))
    assert cardinal is not None
    assert cardinal.parent is None
    stated = stated_candidates(
        cardinal.body, own_names(cardinal), parent_candidates(escoffier)
    )
    assert stated == ("bechamel", "lobster-butter")


@pytest.mark.corpus
def test_every_chain_of_parents_terminates(escoffier):
    """No preparation is its own ancestor, however long the chain."""
    for preparation in escoffier.preparations:
        walked = {preparation.ref.entry}
        current = preparation
        while current is not None and current.parent is not None:
            current = escoffier.find(current.parent)
            if current is not None:
                assert current.ref.entry not in walked, preparation.title
                walked.add(current.ref.entry)


@pytest.mark.corpus
def test_an_ambiguous_base_is_left_unresolved(escoffier):
    """`SHRIMP SAUCE` names velouté and Béchamel. The source chose neither."""
    shrimp = escoffier.find(ConceptId("shrimp-sauce"))
    assert shrimp is not None
    assert shrimp.parent is None


@pytest.mark.corpus
def test_a_meaningful_share_stays_unresolved(escoffier):
    """The honest score. A fall here means the parser started guessing."""
    assert escoffier.unresolved > len(escoffier.preparations) // 2


@pytest.mark.corpus
def test_the_revision_states_the_edition_the_catalogue_is_named_for(escoffier):
    """The string comes from the title page, not from the filename."""
    edition = escoffier.witness.edition
    assert edition.statement == "New and Revised Edition, January 1909"
    assert edition.impression == "January 1920"
    assert edition.copyright_year == 1907
    assert escoffier.source_id == "escoffier-1909"


@pytest.mark.corpus
def test_the_first_printing_states_no_edition_and_falls_back_to_copyright(
    escoffier_1907,
):
    edition = escoffier_1907.witness.edition
    assert edition.statement is None
    assert edition.impression is None
    assert edition.copyright_year == 1907
    assert escoffier_1907.source_id == "escoffier-1907"


@pytest.mark.corpus
def test_every_corpus_file_is_named_for_the_id_read_out_of_it():
    """The filename is a convenience. The document is the evidence."""
    for source in escoffier_sources():
        expected = f"{source.witness.source_id}.txt"
        assert expected in {p.name for p in Paths.discover().corpus.iterdir()}


@pytest.mark.corpus
def test_the_scanned_witness_publishes_its_own_census(
    escoffier_1907, first_printing_census
):
    assert len(escoffier_1907.preparations) == first_printing_census.sauces
    assert escoffier_1907.resolved == first_printing_census.derived
    assert escoffier_1907.unresolved == first_printing_census.unresolved


@pytest.mark.corpus
def test_the_scanned_witness_records_that_it_is_a_scan(escoffier_1907):
    assert escoffier_1907.fidelity == Fidelity.OCR
    assert all(p.ref.fidelity == Fidelity.OCR for p in escoffier_1907.preparations)


@pytest.mark.corpus
def test_the_normalised_scan_still_lands_every_line_reference():
    """The wrapper maps one line to one line, so a citation is checkable.

    The separator on the page is an em dash, or the hyphens or underscore a
    scanner left in its place, so the check reads the number and accepts any
    of them.
    """
    path = Paths.discover().escoffier_scan
    lines = path.read_text(encoding="utf-8").splitlines()
    catalogue = extract(escoffier_sources()[1])
    for preparation in catalogue.preparations:
        found = lines[preparation.ref.line - 1]
        assert re.match(rf"\s*{preparation.ref.entry}\s*(—|-{{1,2}}|_)", found), (
            f"entry {preparation.ref.entry} claims line {preparation.ref.line}, "
            f"which reads {found!r}"
        )


@pytest.mark.corpus
def test_the_ocr_witness_answers_where_the_clean_one_refuses(escoffier, escoffier_1907):
    """ADR-0012's worked example. Neither answer is repaired here."""
    clean = escoffier.find(ConceptId("aurore-sauce"))
    scanned = escoffier_1907.find(ConceptId("aurore-sauce"))
    assert clean is not None
    assert scanned is not None
    assert clean.parent is None
    assert scanned.parent == "tomato"


@pytest.mark.corpus
def test_entry_63_reads_whole_in_both_witnesses(escoffier, escoffier_1907):
    """The heading wraps in both printings, at different points.

    A reader that stopped at the newline recorded two different titles, and
    the diff then blamed the difference on the scanned witness.
    """
    whole = "SAUCE WITH MEAT GLAZE, OTHERWISE VALOIS SAUCE OR FOYOT SAUCE"
    clean = escoffier.find(ConceptId("bearnaise-sauce-with-meat-glaze"))
    scanned = escoffier_1907.find(ConceptId("bearnaise-sauce-with-meat-glaze"))
    assert clean is not None
    assert scanned is not None
    assert clean.title == f"BÉARNAISE {whole}"
    assert scanned.title == f"BEARNAISE {whole}"
    assert clean.concept == scanned.concept


@pytest.mark.corpus
def test_the_number_of_wrapped_headings_is_the_measured_one():
    """Four in the proofread text, 42 in the scan, whose column is narrower.

    A rise here means the rule loosened and is absorbing something else. One
    of the 42 became visible only once its broken separator was repaired.
    """
    joined = []
    for source in escoffier_sources():
        lines = source.lines()
        joined.append(
            sum(
                1
                for index, line in enumerate(lines)
                if ENTRY.match(line) and continues_heading(lines, index + 1)
            )
        )
    assert joined == [4, 42]


@pytest.mark.corpus
def test_a_restored_heading_still_faces_the_dish_rule(escoffier_1907):
    """Entry 1396 gains `OR ROBERT SAUCE` and is still a dish.

    Its `WITH` precedes its `SAUCE`, which is ADR-0007's test, and the test
    runs against the whole title rather than the truncated one.
    """
    titles = {p.title for p in escoffier_1907.preparations}
    assert "FRESH-PORK CUTLETS WITH PIQUANTE OR ROBERT SAUCE" not in titles


RECOVERED = {
    25: "ORDINARY VELOUTE SAUCE",
    33: "CHASSEUR SAUCE (Escoffier's Method)",
    36: "DEVILLED SAUCE",
    37: '"ESCOFFIER" DEVILLED SAUCE',
    57: "VENISON SAUCE",
    69: "CARDINAL SAUCE",
    79: "CREAM SAUCE",
    85: "HUNQARIAN SAUCE",
    102: "RAVIQOTTE SAUCE",
    107: "VENETIAN SAUCE",
    125: "QRIBICHE SAUCE",
    126: "MAYONNAISE SAUCE",
    135: "QLOUCESTER SAUCE",
}
"""Sauces the scan hides behind a broken entry separator, with their titles.

Thirteen of them. Nine behind a hyphen, one behind two, one behind an
underscore, and one held out of an earlier guard by a lower-case
parenthetical.

Each one carries the spelling the scan has. A repaired separator recovers the
record and never touches the word.
"""


@pytest.mark.corpus
def test_every_sauce_behind_a_broken_separator_is_recovered(escoffier_1907):
    found = {p.ref.entry: p.title for p in escoffier_1907.preparations}
    assert {n: found.get(n) for n in RECOVERED} == RECOVERED


@pytest.mark.corpus
def test_mayonnaise_is_in_both_witnesses_and_was_never_added(escoffier, escoffier_1907):
    """Entry 126 in both books. The diff called it an addition for a release."""
    clean = escoffier.find(ConceptId("mayonnaise-sauce"))
    scanned = escoffier_1907.find(ConceptId("mayonnaise-sauce"))
    assert clean is not None
    assert scanned is not None
    assert (clean.ref.entry, scanned.ref.entry) == (126, 126)


@pytest.mark.corpus
def test_the_number_of_repaired_separators_is_the_measured_one():
    """Fifty-seven, every one checked by eye against the page it sits on.

    A rise here means the guard loosened and is admitting prose.
    """
    path = Paths.discover().escoffier_scan
    lines = path.read_text(encoding="utf-8").splitlines()
    cleaned = (normalise(line) for line in lines)
    assert sum(1 for line in cleaned if repair_separator(line) != line) == 57


ADMITTED = {
    19: "BROWN ROUX",
    20: "PALE ROUX",
    21: "WHITE ROUX",
    23: "HALF GLAZE",
    41: "THICKENED GRAVY",
    42: "VEAL GRAVY TOMATÉ",
    97: "SECOND METHOD (WITH COOKED LOBSTER)",
    128: "WHISKED MAYONNAISE",
    139: "BERCY BUTTER",
    140: "CHIVRY OR RAVIGOTE BUTTER",
    141: "COLBERT BUTTER",
    142: "RED COLOURING BUTTER",
    143: "GREEN COLOURING BUTTER",
    144: "VARIOUS CULLISES",
    145: "SHRIMP BUTTER",
    146: "SHALLOT BUTTER",
    147: "CRAYFISH BUTTER",
    148: "TARRAGON BUTTER",
    149: "LOBSTER BUTTER",
    150: "BUTTER A LA MAÎTRE D’HÔTEL",  # noqa: RUF001
    151: "MANIED BUTTER",
    152: "BUTTER A LA MEUNIÈRE",
    153: "MONTPELLIER BUTTER",
    154: "BLACK BUTTER",
    155: "HAZEL-NUT BUTTER",
    156: "PISTACHIO BUTTER",
    157: "PRINTANIER BUTTER",
}
"""The 27 entries the chapter admits in the 1909 text and the heading did not.

Every one sits inside a chapter Escoffier titles as sauces and lacks the
word "sauce" in its heading. Nothing here is hand-picked: entry 97 is a
lobster method the source numbered on its own, and it enters because the
source numbered it. ADR-0015 records the rule.
"""

UNREAD_IN_THE_SCAN = {153: "IS3— MONTPELLIER  BUTTER", 155: "15s— HAZEL-NUT  BUTTER"}
"""Two of the 27 the 1907 scan cannot read, with the heading as the scan has it.

`MONTPELLIER BUTTER` and `HAZEL-NUT BUTTER` are on the page. The scanner
read their entry numbers as letters, so the entry pattern never matches.
That is a corrupted number, and ADR-0013 leaves it unrepaired here.
"""

GAINED = {
    "sauce-bordelaise": "half-glaze",
    "brown-chaud-froid-sauce": "half-glaze",
    "devilled-sauce": "half-glaze",
    "italian-sauce": "half-glaze",
    "lyonnaise-sauce": "half-glaze",
    "madeira-sauce": "half-glaze",
    "piquante-sauce": "half-glaze",
    "robert-sauce": "half-glaze",
    "espagnole": "brown-roux",
    "veloute": "pale-roux",
    "scotch-egg-sauce": "white-roux",
    "mousseuse-sauce": "manied-butter",
}
"""The twelve sauces that gained a parent when the chapter decided.

Each was catalogued and unresolved at v0.3.0, and each stated its base in a
sentence the catalogue could not reach because the base was not catalogued.
"""

LOST = {
    "cardinal-sauce": ("bechamel", "lobster-butter"),
    "nantua-sauce": ("bechamel", "crayfish-butter"),
    "noisette-sauce": ("hollandaise", "hazel-nut-butter"),
    "diplomate-sauce": ("normande-sauce", "lobster-butter"),
    "joinville-sauce": ("normande-sauce", "shrimp-butter", "crayfish-butter"),
    "herb-sauce": ("white-wine-sauce", "shallot-butter"),
    "ravigote-sauce": ("veloute", "shallot-butter"),
    "perigueux-sauce": ("half-glaze", "madeira-sauce"),
    "reform-sauce": ("half-glaze", "ordinary-poivrade-sauce"),
    "chasseur-sauce": ("half-glaze", "tomato"),
}
"""The ten sauces that lost a parent, each with what it now states.

Seven were resolved at v0.3.0 to the first name in their tuple, and lost it
to a butter. Three were resolved to the second name and lost it to half
glaze, which was not catalogued then: PÉRIGUEUX, REFORM, and CHASSEUR.
Admitting the butters and half glaze put another catalogued name in the
opening paragraph, and a resolver may refuse, never rank. The loss is ADR-0012
working. Recovering these means reading the verb a name sits in.
"""


@pytest.mark.corpus
def test_every_unresolved_preparation_states_none_or_more_than_one(
    escoffier, escoffier_1907
):
    """An unresolved parent has one of two reasons, and both are visible.

    A preparation with exactly one stated candidate and no parent would mean
    the bookkeeping discarded a resolution, which the 1907 scan's entry 138
    once caused. No cycle exists in either witness to clear one.
    """
    for catalogue in (escoffier, escoffier_1907):
        candidates = parent_candidates(catalogue)
        for preparation in catalogue.preparations:
            if preparation.parent is not None:
                continue
            stated = stated_candidates(
                preparation.body, own_names(preparation), candidates
            )
            assert len(stated) != 1, (catalogue.source_id, preparation.title)


@pytest.mark.corpus
def test_the_scan_reads_whisked_mayonnaise_under_horse_radish_own_number(
    escoffier_1907,
):
    """Entry 128 reads as 138 in the scan, which is also HORSE-RADISH SAUCE.

    Both are catalogued under 138, at lines 3423 and 3550. Each keeps the
    parent its own paragraph states, because a preparation is identified by
    its line. The number stays as the scan reads it: ADR-0013.
    """
    at_138 = [p for p in escoffier_1907.preparations if p.ref.entry == 138]
    assert [p.title for p in at_138] == ["WHISKED MAYONNAISE", "HORSE-RADISH SAUCE"]
    assert [p.ref.line for p in at_138] == [3423, 3550]
    assert [p.parent for p in at_138] == ["horse-radish", None]


@pytest.mark.corpus
def test_every_entry_the_chapter_admits_is_catalogued(escoffier):
    found = {p.ref.entry: p.title for p in escoffier.preparations}
    assert {n: found.get(n) for n in ADMITTED} == ADMITTED


@pytest.mark.corpus
def test_the_scan_reads_the_butter_headings_it_can(escoffier_1907):
    """25 of the 27 in the scan. The two it cannot read are named, not lost."""
    found = {p.ref.entry for p in escoffier_1907.preparations}
    readable = set(ADMITTED) - set(UNREAD_IN_THE_SCAN)
    # The scan reads entry 128 as 138, so WHISKED MAYONNAISE is read under
    # a number it does not carry on the page.
    readable.discard(128)
    assert readable <= found
    assert not set(UNREAD_IN_THE_SCAN) & found
    scan = Paths.discover().escoffier_scan.read_text(encoding="utf-8")
    for heading in UNREAD_IN_THE_SCAN.values():
        assert heading in scan
    titles = {p.title for p in escoffier_1907.preparations}
    assert "WHISKED MAYONNAISE" in titles
    assert "MONTPELLIER BUTTER" not in titles
    assert "HAZEL-NUT BUTTER" not in titles


@pytest.mark.corpus
def test_the_twelve_gained_parents_are_the_ones_escoffier_wrote(escoffier):
    for concept, parent in GAINED.items():
        found = escoffier.find(ConceptId(concept))
        assert found is not None, concept
        assert found.parent == parent, concept


@pytest.mark.corpus
def test_the_ten_lost_parents_each_state_more_than_one_candidate(escoffier):
    """Each refusal is checkable: the paragraph names every one, in this order."""
    candidates = parent_candidates(escoffier)
    for concept, stated in LOST.items():
        found = escoffier.find(ConceptId(concept))
        assert found is not None, concept
        assert found.parent is None, concept
        assert stated_candidates(found.body, own_names(found), candidates) == stated


@pytest.mark.corpus
def test_the_census_moved_by_the_three_numbers_the_docs_name(escoffier, census):
    """The seven is not one number.

    50 is the v0.3.0 derived count, a literal because that tag is immutable.
    The measured quantities are the catalogue's own count, the five admitted
    entries that state a parent, and the two tables above.
    """
    admitted_resolved = [
        p
        for p in escoffier.preparations
        if p.ref.entry in ADMITTED and p.parent is not None
    ]
    assert len(admitted_resolved) == 5
    assert escoffier.resolved == census.derived
    assert escoffier.resolved == 50 + len(GAINED) - len(LOST) + len(admitted_resolved)


MORNAY_VERBS = ("Boil", "Reduce", "add", "Put", "stirring", "Finish")
"""The six operations Mornay states, as each witness writes the verb.

Lines 2439 to 2446 of the 1909 text, and 2866 to 2878 of the scan. The
verbs keep the case the source gives them, because a wording quotes.
"""


def recorded_in(catalogue):
    """Every preparation of a catalogue with a recorded procedure, checked."""
    recorded = HandProcedures()
    found = []
    for preparation in catalogue.preparations:
        procedure = procedure_of(preparation, recorded)
        if procedure is not None:
            found.append((preparation, procedure))
    return found


def recorded_procedure(catalogue, concept):
    """The checked procedure of one preparation, which has to have one."""
    preparation = catalogue.find(ConceptId(concept))
    assert preparation is not None, concept
    procedure = procedure_of(preparation, HandProcedures())
    assert procedure is not None, concept
    return preparation, procedure


def measured(parameter):
    """The number and unit of a parameter that has to be stated."""
    assert parameter is not None
    return parameter.number, parameter.unit


@pytest.mark.corpus
def test_one_preparation_per_witness_carries_a_recorded_procedure(
    escoffier, escoffier_1907
):
    """The published count of recorded preparations, and it is one.

    A change that records a second preparation adds its hand check here in
    the same change, or fails. ADR-0017 records the rule.
    """
    assert [(p.ref.entry, p.ref.line) for p, _ in recorded_in(escoffier)] == [
        (91, 2437)
    ]
    assert [(p.ref.entry, p.ref.line) for p, _ in recorded_in(escoffier_1907)] == [
        (91, 2864)
    ]


@pytest.mark.corpus
def test_mornay_states_six_operations_in_the_order_the_body_states_them(escoffier):
    _, procedure = recorded_procedure(escoffier, "mornay-sauce")
    assert tuple(op.verb.surface for op in procedure.operations) == MORNAY_VERBS


@pytest.mark.corpus
def test_mornay_first_operation_takes_its_parent(escoffier):
    """The derivation has a verb. Boil one pint of it, with a quarter pint of fumet."""
    mornay, procedure = recorded_procedure(escoffier, "mornay-sauce")
    bechamel, fumet = procedure.operations[0].inputs
    assert mornay.parent == "bechamel"
    assert escoffier.find(bechamel.term.concept) is escoffier.find(mornay.parent)
    assert measured(bechamel.quantity) == (1, "pint")
    assert measured(fumet.quantity) == (Fraction(1, 4), "pint")
    assert fumet.term.surface == "fumet"


@pytest.mark.corpus
def test_a_stated_number_is_recorded_and_an_unstated_one_is_unresolved(escoffier):
    """Two oz. three times. `a few minutes` is a duration with no number."""
    _, procedure = recorded_procedure(escoffier, "mornay-sauce")
    reduce, add, put, stir, finish = procedure.operations[1:]
    assert [
        (i.term.surface, *measured(i.quantity)) for i in add.inputs + finish.inputs
    ] == [("Gruyère", 2, "oz."), ("Parmesan", 2, "oz."), ("butter", 2, "oz.")]
    assert reduce.criterion is not None
    assert reduce.criterion.wording == "by a good quarter"
    assert measured(reduce.criterion) == (None, None)
    assert put.duration is not None
    assert put.duration.wording == "a few minutes"
    assert measured(put.duration) == (None, "minutes")
    assert put.constraints == ("on the fire again",)
    assert stir.instrument is not None
    assert stir.instrument.surface == "small whisk"
    assert stir.criterion is not None
    assert stir.criterion.wording == "the melting of the cheese"
    assert finish.constraints == ("away from the fire", "added by degrees")


@pytest.mark.corpus
def test_the_scan_states_the_same_operations_and_cannot_name_the_parent(
    escoffier_1907,
):
    """`MORN AY SAUCE` at line 2864. Its Béchamel reads `Bdchamel`.

    The scanner broke the heading and the parent's name. The verb survived,
    and so did every quantity. The reduce clause crosses a page break, so
    its wording carries the running header the scan puts there.
    """
    scanned, procedure = recorded_procedure(escoffier_1907, "morn-ay-sauce")
    assert scanned.title == "MORN AY SAUCE"
    assert scanned.parent is None
    assert tuple(op.verb.surface for op in procedure.operations) == MORNAY_VERBS
    bechamel = procedure.operations[0].inputs[0]
    assert bechamel.term.surface == "Bdchamel Sauce"
    assert escoffier_1907.find(bechamel.term.concept) is None
    assert procedure.operations[2].inputs[0].term.surface == "Gruy^re"
    assert "40 GUIDE TO MODERN COOKERY" in procedure.operations[1].wording


@pytest.mark.corpus
def test_the_revision_widened_mornay_from_fish_to_fish_poultry_or_vegetable(
    escoffier, escoffier_1907
):
    """The first editorial difference confirmed between the two printings.

    Line 2866 of the scan reads `of that fish`. Line 2438 of the revision
    reads `of the fish, poultry, or vegetable`. No scanner adds two nouns.
    The other five operations read the same in both, and the last three
    word for word.
    """
    _, clean = recorded_procedure(escoffier, "mornay-sauce")
    _, scanned = recorded_procedure(escoffier_1907, "morn-ay-sauce")
    clean_fumet = clean.operations[0].inputs[1]
    scanned_fumet = scanned.operations[0].inputs[1]
    assert "of the fish, poultry, or vegetable, which is" in clean_fumet.wording
    assert "of that fish which is" in scanned_fumet.wording
    assert clean_fumet.term == scanned_fumet.term
    assert clean_fumet.quantity == scanned_fumet.quantity
    assert clean.operations[3:] == scanned.operations[3:]
