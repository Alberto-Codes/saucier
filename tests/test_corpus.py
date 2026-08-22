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

import pytest

from saucier.domain.types import ConceptId
from saucier.domain.witness import Fidelity
from saucier.infrastructure.bootstrap import escoffier_sources
from saucier.infrastructure.config import Paths
from saucier.services.extraction import ENTRY, continues_heading, extract


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
def test_espagnole_is_present_and_is_its_own_root(escoffier):
    espagnole = escoffier.find(ConceptId("espagnole"))
    assert espagnole is not None
    assert espagnole.parent is None
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
def test_bordelaise_stays_unresolved_on_the_half_glaze_trap(escoffier):
    """Entry 32 names half-glaze, which encodes a derivation but states none."""
    bordelaise = escoffier.find(ConceptId("bordelaise"))
    assert bordelaise is not None
    assert bordelaise.title == "SAUCE BORDELAISE"
    assert bordelaise.parent is None


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
    """The wrapper maps one line to one line, so a citation is checkable."""
    path = Paths.discover().escoffier_scan
    lines = path.read_text(encoding="utf-8").splitlines()
    catalogue = extract(escoffier_sources()[1])
    for preparation in catalogue.preparations:
        found = lines[preparation.ref.line - 1]
        assert f"{preparation.ref.entry}—" in found, (
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
    """Four in the proofread text, 41 in the scan, whose column is narrower.

    A rise here means the rule loosened and is absorbing something else.
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
    assert joined == [4, 41]


@pytest.mark.corpus
def test_a_restored_heading_still_faces_the_dish_rule(escoffier_1907):
    """Entry 1396 gains `OR ROBERT SAUCE` and is still a dish.

    Its `WITH` precedes its `SAUCE`, which is ADR-0007's test, and the test
    runs against the whole title rather than the truncated one.
    """
    titles = {p.title for p in escoffier_1907.preparations}
    assert "FRESH-PORK CUTLETS WITH PIQUANTE OR ROBERT SAUCE" not in titles
