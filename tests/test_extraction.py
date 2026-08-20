import pytest

from saucier.domain.types import Language, to_concept_id
from saucier.services.extraction import (
    find_mothers,
    is_sauce,
    iter_entries,
    resolve_parent,
    terms_in,
)

MOTHERS = frozenset(to_concept_id(m) for m in ["espagnole", "veloute", "bechamel"])


@pytest.mark.unit
def test_alternative_names_become_separate_terms():
    terms = terms_in("BROWN SAUCE OR ESPAGNOLE")
    assert [t.surface for t in terms] == ["BROWN SAUCE", "ESPAGNOLE"]


@pytest.mark.unit
def test_a_term_is_never_translated_only_tagged():
    (term,) = terms_in("SAUCE BIGARRADE")
    assert term.surface == "SAUCE BIGARRADE"
    assert term.language is Language.FRENCH


@pytest.mark.unit
@pytest.mark.parametrize(
    ("title", "language"),
    [
        ("ORDINARY VELOUTÉ SAUCE", Language.FRENCH),
        ("SAUCE BORDELAISE", Language.FRENCH),
        ("ESPAGNOLE", Language.FRENCH),
        ("BROWN SAUCE", Language.ENGLISH),
        ("MARROW SAUCE", Language.ENGLISH),
    ],
)
def test_language_is_inferred_from_diacritics_word_order_and_lexicon(title, language):
    assert terms_in(title)[0].language is language


@pytest.mark.unit
def test_mothers_are_read_from_the_source_not_hardcoded():
    body = (
        "7. The basic sauces: Espagnole, Velouté, Béchamel, Tomato, and\nHollandaise."
    )
    assert find_mothers(body) == frozenset(
        {"espagnole", "veloute", "bechamel", "tomato", "hollandaise"}
    )


@pytest.mark.unit
def test_a_source_naming_no_mothers_yields_none():
    assert find_mothers("nothing of the sort here") == frozenset()


@pytest.mark.unit
@pytest.mark.parametrize(
    ("title", "keep"),
    [
        ("MADEIRA SAUCE", True),
        ("LENTEN ESPAGNOLE", True),
        ("ASPARAGUS WITH VARIOUS SAUCES", False),
        ("ARTICHOKES WITH DIVERS SAUCES", False),
        ("BROWN STOCK", False),
    ],
)
def test_dishes_that_take_a_sauce_are_not_sauces(title, keep):
    assert is_sauce(title, MOTHERS) is keep


@pytest.mark.unit
def test_entries_split_on_the_numbered_heading():
    lines = ["22—BROWN SAUCE", "body one", "", "23—HALF GLAZE", "body two"]
    entries = list(iter_entries(lines))
    assert [(n, t) for n, _, t, _ in entries] == [
        (22, "BROWN SAUCE"),
        (23, "HALF GLAZE"),
    ]
    assert entries[0][3] == "body one"


@pytest.mark.unit
def test_a_preparation_is_never_its_own_parent():
    own = frozenset({to_concept_id("espagnole")})
    assert resolve_parent("Dissolve the espagnole.", own, MOTHERS) is None


@pytest.mark.unit
def test_only_the_opening_paragraph_establishes_a_base():
    body = "Reduce the wine.\n\nUnlike the espagnole, this sauce is not despumated."
    assert resolve_parent(body, frozenset(), MOTHERS) is None


@pytest.mark.unit
def test_a_base_named_in_the_opening_paragraph_resolves():
    body = "Add one pint of espagnole to the reduction.\n\nSeason and strain."
    assert resolve_parent(body, frozenset(), MOTHERS) == "espagnole"


@pytest.mark.unit
def test_an_entry_with_no_prose_resolves_to_nothing():
    assert resolve_parent("", frozenset(), MOTHERS) is None
