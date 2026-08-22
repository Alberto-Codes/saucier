import pytest
from conftest import a_witness

from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
from saucier.domain.types import ConceptId, Language
from saucier.domain.witness import Fidelity

WITNESS = a_witness()


def preparation(title, parent=None, surfaces=None, entry=1):
    surfaces = surfaces or [title]
    return Preparation(
        title=title,
        terms=tuple(Term(s, Language.ENGLISH) for s in surfaces),
        body="",
        ref=SourceRef(
            source_id=WITNESS.source_id,
            entry=entry,
            line=entry,
            fidelity=WITNESS.fidelity,
        ),
        parent=ConceptId(parent) if parent else None,
    )


@pytest.mark.unit
def test_a_term_derives_its_concept_from_its_surface():
    assert Term("Velouté", Language.FRENCH).concept == "veloute"


@pytest.mark.unit
def test_a_source_reference_must_name_a_checkable_location():
    with pytest.raises(ValueError, match="1 or greater"):
        SourceRef(source_id="test", entry=0, line=5, fidelity=Fidelity.OCR)
    with pytest.raises(ValueError, match="1 or greater"):
        SourceRef(source_id="test", entry=5, line=-1, fidelity=Fidelity.OCR)
    with pytest.raises(ValueError, match="needs a source id"):
        SourceRef(source_id="  ", entry=1, line=1, fidelity=Fidelity.OCR)


@pytest.mark.unit
def test_a_source_reference_is_keyword_only_so_it_cannot_be_transposed():
    # ty flags this call too, which is the point: the guard holds at both
    # check time and run time.
    with pytest.raises(TypeError):
        SourceRef("test", 1, 1, Fidelity.OCR)  # ty: ignore[missing-argument, too-many-positional-arguments]


@pytest.mark.unit
def test_an_unresolved_parent_must_be_stated_not_defaulted():
    with pytest.raises(TypeError):
        Preparation(  # ty: ignore[missing-argument]
            title="A",
            terms=(),
            body="",
            ref=SourceRef(source_id="test", entry=1, line=1, fidelity=Fidelity.OCR),
        )


@pytest.mark.unit
def test_a_preparation_answers_to_every_name_it_carries():
    catalogue = Catalogue(
        witness=WITNESS,
        preparations=(
            preparation(
                "BROWN SAUCE OR ESPAGNOLE", surfaces=["BROWN SAUCE", "ESPAGNOLE"]
            ),
        ),
    )
    index = catalogue.by_concept()
    assert index[ConceptId("brown-sauce")] is index[ConceptId("espagnole")]


@pytest.mark.unit
def test_lookup_falls_back_to_a_whole_word_run():
    catalogue = Catalogue(
        witness=WITNESS, preparations=(preparation("SAUCE BORDELAISE"),)
    )
    found = catalogue.find(ConceptId("bordelaise"))
    assert found is not None
    assert found.title == "SAUCE BORDELAISE"


@pytest.mark.unit
def test_lookup_prefers_the_least_qualified_name():
    catalogue = Catalogue(
        witness=WITNESS,
        preparations=(
            preparation("WHITE BORDELAISE SAUCE", entry=1),
            preparation("SAUCE BORDELAISE", entry=2),
        ),
    )
    found = catalogue.find(ConceptId("bordelaise"))
    assert found is not None
    assert found.title == "SAUCE BORDELAISE"


@pytest.mark.unit
def test_a_mother_binds_to_the_first_preparation_answering_to_it():
    """The source states a base before its derivatives, so order decides."""
    catalogue = Catalogue(
        witness=WITNESS,
        preparations=(
            preparation("ORDINARY VELOUTÉ SAUCE", entry=1),
            preparation("THICKENED VELOUTÉ", entry=2),
        ),
        mothers=frozenset({ConceptId("veloute")}),
    )
    found = catalogue.find(ConceptId("veloute"))
    assert found is not None
    assert found.title == "ORDINARY VELOUTÉ SAUCE"


@pytest.mark.unit
def test_lookup_breaks_a_remaining_tie_by_source_order():
    catalogue = Catalogue(
        witness=WITNESS,
        preparations=(
            preparation("EARLY BORDELAISE", entry=1),
            preparation("LATER BORDELAISE", entry=2),
        ),
    )
    assert [p.title for p in catalogue.matches(ConceptId("bordelaise"))] == [
        "EARLY BORDELAISE",
        "LATER BORDELAISE",
    ]


@pytest.mark.unit
def test_a_word_run_must_match_whole_words():
    catalogue = Catalogue(
        witness=WITNESS, preparations=(preparation("GRILLED TOMATOES"),)
    )
    assert catalogue.find(ConceptId("tomato")) is None


@pytest.mark.unit
def test_lookup_returns_nothing_rather_than_guessing():
    catalogue = Catalogue(witness=WITNESS, preparations=(preparation("MARROW SAUCE"),))
    assert catalogue.find(ConceptId("mole")) is None


@pytest.mark.unit
def test_children_come_back_in_source_order():
    catalogue = Catalogue(
        witness=WITNESS,
        preparations=(
            preparation("FIRST", parent="espagnole", entry=1),
            preparation("SECOND", parent="veloute", entry=2),
            preparation("THIRD", parent="espagnole", entry=3),
        ),
    )
    titles = [p.title for p in catalogue.children_of(ConceptId("espagnole"))]
    assert titles == ["FIRST", "THIRD"]


@pytest.mark.unit
def test_resolved_and_unresolved_partition_the_catalogue():
    catalogue = Catalogue(
        witness=WITNESS,
        preparations=(
            preparation("A", parent="espagnole", entry=1),
            preparation("B", entry=2),
            preparation("C", entry=3),
        ),
    )
    assert catalogue.resolved == 1
    assert catalogue.unresolved == 2
    assert catalogue.resolved + catalogue.unresolved == len(catalogue.preparations)


@pytest.mark.unit
def test_preparations_are_frozen():
    with pytest.raises((AttributeError, TypeError)):
        preparation("A").title = "B"


@pytest.mark.unit
def test_a_reference_states_the_fidelity_of_the_text_it_points_into():
    ref = SourceRef(source_id="escoffier-1907", entry=1, line=1, fidelity=Fidelity.OCR)
    assert ref.fidelity == "ocr"


@pytest.mark.unit
def test_a_catalogue_refuses_a_record_that_contradicts_its_witness():
    """Fidelity is recorded twice, so the two may never disagree."""
    scanned = SourceRef(
        source_id=WITNESS.source_id, entry=1, line=1, fidelity=Fidelity.OCR
    )
    with pytest.raises(ValueError, match="in a catalogue of"):
        Catalogue(
            witness=WITNESS,
            preparations=(
                Preparation(title="A", terms=(), body="", ref=scanned, parent=None),
            ),
        )


@pytest.mark.unit
def test_a_catalogue_refuses_a_record_citing_another_source():
    stranger = SourceRef(
        source_id="another-1800", entry=1, line=1, fidelity=WITNESS.fidelity
    )
    with pytest.raises(ValueError, match="cites another-1800"):
        Catalogue(
            witness=WITNESS,
            preparations=(
                Preparation(title="A", terms=(), body="", ref=stranger, parent=None),
            ),
        )


@pytest.mark.unit
def test_a_catalogue_reports_the_identity_of_its_witness():
    catalogue = Catalogue(witness=WITNESS)
    assert catalogue.source_id == WITNESS.source_id
    assert catalogue.fidelity == WITNESS.fidelity
