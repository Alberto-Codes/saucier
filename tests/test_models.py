import pytest

from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
from saucier.domain.types import ConceptId, Language


def preparation(title, parent=None, surfaces=None, entry=1):
    surfaces = surfaces or [title]
    return Preparation(
        title=title,
        terms=tuple(Term(s, Language.ENGLISH) for s in surfaces),
        body="",
        ref=SourceRef(source_id="test", entry=entry, line=entry),
        parent=ConceptId(parent) if parent else None,
    )


@pytest.mark.unit
def test_a_term_derives_its_concept_from_its_surface():
    assert Term("Velouté", Language.FRENCH).concept == "veloute"


@pytest.mark.unit
def test_a_source_reference_must_name_a_checkable_location():
    with pytest.raises(ValueError, match="1 or greater"):
        SourceRef(source_id="test", entry=0, line=5)
    with pytest.raises(ValueError, match="1 or greater"):
        SourceRef(source_id="test", entry=5, line=-1)
    with pytest.raises(ValueError, match="needs a source id"):
        SourceRef(source_id="  ", entry=1, line=1)


@pytest.mark.unit
def test_a_source_reference_is_keyword_only_so_it_cannot_be_transposed():
    # ty flags this call too, which is the point: the guard holds at both
    # check time and run time.
    with pytest.raises(TypeError):
        SourceRef("test", 1, 1)  # ty: ignore[missing-argument, too-many-positional-arguments]


@pytest.mark.unit
def test_an_unresolved_parent_must_be_stated_not_defaulted():
    with pytest.raises(TypeError):
        Preparation(  # ty: ignore[missing-argument]
            title="A",
            terms=(),
            body="",
            ref=SourceRef(source_id="test", entry=1, line=1),
        )


@pytest.mark.unit
def test_a_preparation_answers_to_every_name_it_carries():
    catalogue = Catalogue(
        source_id="test",
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
        source_id="test", preparations=(preparation("SAUCE BORDELAISE"),)
    )
    found = catalogue.find(ConceptId("bordelaise"))
    assert found is not None
    assert found.title == "SAUCE BORDELAISE"


@pytest.mark.unit
def test_lookup_prefers_the_least_qualified_name():
    catalogue = Catalogue(
        source_id="test",
        preparations=(
            preparation("WHITE BORDELAISE SAUCE", entry=1),
            preparation("SAUCE BORDELAISE", entry=2),
        ),
    )
    found = catalogue.find(ConceptId("bordelaise"))
    assert found is not None
    assert found.title == "SAUCE BORDELAISE"


@pytest.mark.unit
def test_lookup_breaks_a_remaining_tie_by_source_order():
    catalogue = Catalogue(
        source_id="test",
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
        source_id="test", preparations=(preparation("GRILLED TOMATOES"),)
    )
    assert catalogue.find(ConceptId("tomato")) is None


@pytest.mark.unit
def test_lookup_returns_nothing_rather_than_guessing():
    catalogue = Catalogue(source_id="test", preparations=(preparation("MARROW SAUCE"),))
    assert catalogue.find(ConceptId("mole")) is None


@pytest.mark.unit
def test_children_come_back_in_source_order():
    catalogue = Catalogue(
        source_id="test",
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
        source_id="test",
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
