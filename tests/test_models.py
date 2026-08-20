import pytest

from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
from saucier.domain.types import ConceptId, Language


def preparation(title, parent=None, surfaces=None):
    surfaces = surfaces or [title]
    return Preparation(
        title=title,
        terms=tuple(Term.of(s, Language.ENGLISH) for s in surfaces),
        body="",
        ref=SourceRef("test", 1, 1),
        parent=ConceptId(parent) if parent else None,
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
def test_lookup_falls_back_to_a_name_ending_match():
    catalogue = Catalogue(
        source_id="test", preparations=(preparation("SAUCE BORDELAISE"),)
    )
    found = catalogue.find(ConceptId("bordelaise"))
    assert found is not None
    assert found.title == "SAUCE BORDELAISE"


@pytest.mark.unit
def test_lookup_returns_nothing_rather_than_guessing():
    catalogue = Catalogue(source_id="test", preparations=(preparation("MARROW SAUCE"),))
    assert catalogue.find(ConceptId("mole")) is None


@pytest.mark.unit
def test_children_come_back_in_source_order():
    catalogue = Catalogue(
        source_id="test",
        preparations=(
            preparation("FIRST", parent="espagnole"),
            preparation("SECOND", parent="veloute"),
            preparation("THIRD", parent="espagnole"),
        ),
    )
    titles = [p.title for p in catalogue.children_of(ConceptId("espagnole"))]
    assert titles == ["FIRST", "THIRD"]


@pytest.mark.unit
def test_resolved_counts_only_preparations_with_a_parent():
    catalogue = Catalogue(
        source_id="test",
        preparations=(preparation("A", parent="espagnole"), preparation("B")),
    )
    assert catalogue.resolved == 1


@pytest.mark.unit
def test_preparations_are_frozen():
    with pytest.raises((AttributeError, TypeError)):
        preparation("A").title = "B"
