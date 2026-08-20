"""Tests against the committed Escoffier text.

These lock in what the source actually says, so a parser change that quietly
loses preparations, or quietly gains some, fails here rather than in a blog
post.

The published counts live in `conftest.CENSUS`. Changing them is a deliberate
act: update the README, the tutorial, and the documentation home page in the
same commit, and say why in the changelog.
"""

import pytest

from saucier.domain.types import ConceptId
from saucier.infrastructure.config import Paths


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
    lines = Paths.discover().escoffier.read_text(encoding="utf-8").splitlines()
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
def test_a_recorded_parent_is_always_in_the_catalogue(escoffier):
    for preparation in escoffier.preparations:
        if preparation.parent is not None:
            found = escoffier.find(preparation.parent)
            assert found is not None or preparation.parent in escoffier.mothers


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
