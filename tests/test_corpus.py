"""Tests against the committed Escoffier text.

These lock in what the source actually says, so a parser change that quietly
loses preparations fails here rather than in a blog post.
"""

import pytest

from saucier.domain.types import ConceptId


@pytest.mark.corpus
def test_the_source_names_its_own_five_base_sauces(escoffier):
    assert escoffier.mothers == frozenset(
        {"espagnole", "veloute", "bechamel", "tomato", "hollandaise"}
    )


@pytest.mark.corpus
def test_the_catalogue_is_substantial(escoffier):
    assert len(escoffier.preparations) > 100


@pytest.mark.corpus
def test_espagnole_is_present_and_is_its_own_root(escoffier):
    espagnole = escoffier.find(ConceptId("espagnole"))
    assert espagnole is not None
    assert espagnole.parent is None
    assert espagnole not in escoffier.children_of(ConceptId("espagnole"))


@pytest.mark.corpus
def test_french_terms_survive_untranslated(escoffier):
    bordelaise = escoffier.find(ConceptId("bordelaise"))
    assert bordelaise is not None
    assert bordelaise.title == "SAUCE BORDELAISE"


@pytest.mark.corpus
def test_every_preparation_is_traceable_to_a_line(escoffier):
    assert all(p.ref.line > 0 and p.ref.entry > 0 for p in escoffier.preparations)


@pytest.mark.corpus
def test_no_dish_entries_leaked_into_the_sauce_catalogue(escoffier):
    titles = [p.title.upper() for p in escoffier.preparations]
    assert not [t for t in titles if " WITH " in t]


@pytest.mark.corpus
def test_a_meaningful_share_stays_unresolved(escoffier):
    """The honest score. A rise here means the parser started guessing."""
    unresolved = len(escoffier.preparations) - escoffier.resolved
    assert unresolved > 0
