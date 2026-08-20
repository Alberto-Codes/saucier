import pytest

from saucier.domain.errors import NoPreparationsFound
from saucier.domain.types import Language, to_concept_id
from saucier.services.extraction import (
    Candidate,
    extract,
    find_mothers,
    is_sauce,
    iter_entries,
    names_a_sauce,
    parent_candidates,
    resolve_parent,
    sauce_chapters,
    terms_in,
)

MOTHERS = frozenset(to_concept_id(m) for m in ["espagnole", "veloute", "bechamel"])

CANDIDATES = {m: Candidate(m, m, mother=True) for m in MOTHERS}
"""Mothers alone, the smallest candidate set a source can declare."""


class FakeSource:
    """A source of the smallest shape the port accepts."""

    def __init__(self, lines, source_id="fixture", line_offset=0):
        """Hold the lines a fake source hands back."""
        self._lines = lines
        self.source_id = source_id
        self.line_offset = line_offset

    def lines(self):
        return list(self._lines)


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
        # The lexicon is tested word by word, not against the whole heading.
        ("HOLLANDAISE SAUCE", Language.FRENCH),
        ("BROWN SAUCE", Language.ENGLISH),
        ("MARROW SAUCE", Language.ENGLISH),
    ],
)
def test_language_is_inferred_from_diacritics_word_order_and_lexicon(title, language):
    assert terms_in(title)[0].language is language


@pytest.mark.unit
@pytest.mark.parametrize(
    "title",
    # The curly punctuation is the point: it is not a diacritic.
    ["“ESCOFFIER” CHERRY SAUCE", "CHASSEUR SAUCE (Escoffier’s Method)"],  # noqa: RUF001
)
def test_typographic_punctuation_is_not_a_diacritic(title):
    assert terms_in(title)[0].language is Language.ENGLISH


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
    ("title", "says_sauce"),
    [
        ("MADEIRA SAUCE", True),
        # A sauce served with something is still a sauce.
        ("SOUBISE SAUCE WITH RICE", True),
        ("EGG SAUCE WITH MELTED BUTTER", True),
        ("ASPARAGUS WITH VARIOUS SAUCES", False),
        ("ARTICHOKES WITH DIVERS SAUCES", False),
        # A heading that names its sauce after a comma names an accompaniment.
        ("MAQUEREAU BOUILLI, SAUCE AUX GROSEILLES", False),
        ("SAUCES AND ACCOMPANIMENTS OF COLD SWEETS", False),
        ("BROWN STOCK", False),
    ],
)
def test_a_heading_that_calls_itself_a_sauce(title, says_sauce):
    assert names_a_sauce(title) is says_sauce


@pytest.mark.unit
@pytest.mark.parametrize(
    ("title", "in_chapter", "keep"),
    [
        ("MADEIRA SAUCE", False, True),
        # A mother in the heading counts only inside a sauce chapter.
        ("LENTEN ESPAGNOLE", True, True),
        ("LENTEN ESPAGNOLE", False, False),
        ("TOMATO SALAD", False, False),
        # Substring matching used to admit these; word matching does not.
        ("GRILLED TOMATOES", True, False),
        ("VELOUTÉ AGNÈS SOREL", False, False),
        ("BROWN STOCK", True, False),
    ],
)
def test_only_the_source_own_evidence_admits_an_entry(title, in_chapter, keep):
    mothers = MOTHERS | {to_concept_id("tomato")}
    assert is_sauce(title, mothers, in_chapter) is keep


@pytest.mark.unit
def test_sauce_chapters_are_read_from_the_chapter_titles():
    lines = [
        "CHAPTER I",
        "",
        "FONDS DE CUISINE",
        "CHAPTER II",
        "",
        "THE LEADING WARM SAUCES",
        "body",
        "CHAPTER III",
        "",
        "SOUPS",
    ]
    assert sauce_chapters(lines) == ((3, 7),)


@pytest.mark.unit
def test_entries_split_on_the_numbered_heading():
    lines = ["22—BROWN SAUCE", "body one", "", "23—HALF GLAZE", "body two"]
    entries = list(iter_entries(lines))
    assert entries == [
        (22, 0, "BROWN SAUCE", "body one"),
        (23, 3, "HALF GLAZE", "body two"),
    ]


@pytest.mark.unit
def test_a_preparation_is_never_its_own_parent():
    own = frozenset({to_concept_id("espagnole")})
    assert resolve_parent("Dissolve the espagnole.", own, CANDIDATES) is None


@pytest.mark.unit
def test_only_the_opening_paragraph_establishes_a_base():
    body = "Reduce the wine.\n\nUnlike the espagnole, this sauce is not despumated."
    assert resolve_parent(body, frozenset(), CANDIDATES) is None


@pytest.mark.unit
def test_a_base_named_in_the_opening_paragraph_resolves():
    body = "Add one pint of espagnole to the reduction.\n\nSeason and strain."
    assert resolve_parent(body, frozenset(), CANDIDATES) == "espagnole"


@pytest.mark.unit
def test_two_bases_in_one_paragraph_resolve_to_nothing():
    body = "Boil one pint of fish velouté or, failing this, Béchamel sauce."
    assert resolve_parent(body, frozenset(), CANDIDATES) is None


@pytest.mark.unit
def test_a_mother_must_appear_as_a_whole_word():
    candidates = {
        to_concept_id("tomato"): Candidate(
            to_concept_id("tomato"), to_concept_id("tomato"), mother=True
        )
    }
    assert resolve_parent("Peel a pound of tomatoes.", frozenset(), candidates) is None


@pytest.mark.unit
def test_an_entry_with_no_prose_resolves_to_nothing():
    assert resolve_parent("", frozenset(), CANDIDATES) is None


@pytest.mark.unit
def test_a_catalogued_preparation_may_be_a_parent():
    candidates = {
        to_concept_id("sauce-bordelaise"): Candidate(
            32, to_concept_id("sauce-bordelaise"), False
        )
    }
    body = "Follow the proportions indicated under Sauce Bordelaise."
    assert resolve_parent(body, frozenset({45}), candidates) == "sauce-bordelaise"


@pytest.mark.unit
def test_a_name_split_across_a_full_stop_is_not_a_statement():
    candidates = {
        to_concept_id("sauce-bordelaise"): Candidate(
            32, to_concept_id("sauce-bordelaise"), False
        )
    }
    body = "Strain the sauce. Bordelaise butter follows in the next entry."
    assert resolve_parent(body, frozenset(), candidates) is None


@pytest.mark.unit
def test_a_longer_stated_name_shadows_the_mother_inside_it():
    candidates = dict(CANDIDATES)
    candidates[to_concept_id("lenten-espagnole")] = Candidate(
        24, to_concept_id("lenten-espagnole"), False
    )
    body = "Add one pint of Lenten Espagnole, and allow to cook."
    assert resolve_parent(body, frozenset(), candidates) == "lenten-espagnole"


@pytest.mark.unit
def test_a_mother_stated_by_its_entry_name_records_the_mother():
    candidates = dict(CANDIDATES)
    candidates[to_concept_id("bechamel")] = Candidate(
        28, to_concept_id("bechamel"), mother=True
    )
    candidates[to_concept_id("bechamel-sauce")] = Candidate(
        28, to_concept_id("bechamel-sauce"), False
    )
    body = "Add one pint of Béchamel Sauce and reduce."
    assert resolve_parent(body, frozenset(), candidates) == "bechamel"


@pytest.mark.unit
def test_a_run_inside_the_entry_own_name_states_no_parent():
    candidates = {
        to_concept_id("horse-radish"): Candidate(
            119, to_concept_id("horse-radish"), False
        )
    }
    own = frozenset({138, to_concept_id("horse-radish-sauce")})
    body = "Add one lb. of finely-rasped horse-radish and one pint of cream."
    assert resolve_parent(body, own, candidates) is None


@pytest.mark.unit
def test_candidates_come_from_the_catalogue_and_the_mothers():
    source = FakeSource(
        [
            "The basic sauces: Espagnole.",
            "22—BROWN SAUCE",
            "Reduce the wine.",
            "",
            "23—MADEIRA SAUCE",
            "Add espagnole.",
        ]
    )
    candidates = parent_candidates(extract(source))
    assert candidates[to_concept_id("madeira-sauce")] == Candidate(
        23, to_concept_id("madeira-sauce"), False
    )
    assert candidates[to_concept_id("espagnole")].mother is True


@pytest.mark.unit
def test_two_preparations_deriving_from_each_other_resolve_to_nothing():
    source = FakeSource(
        [
            "22—ONION SAUCE",
            "Blend with the caper sauce.",
            "",
            "23—CAPER SAUCE",
            "Blend with the onion sauce.",
        ]
    )
    first, second = extract(source).preparations
    assert first.parent is None
    assert second.parent is None


@pytest.mark.unit
def test_a_chain_of_stated_parents_terminates():
    source = FakeSource(
        [
            "22—ONION SAUCE",
            "Reduce the wine.",
            "",
            "23—CAPER SAUCE",
            "Add the onion sauce.",
            "",
            "24—MARROW SAUCE",
            "A variety of the caper sauce.",
        ]
    )
    catalogue = extract(source)
    onion, caper, marrow = catalogue.preparations
    assert onion.parent is None
    assert caper.parent == "onion-sauce"
    assert marrow.parent == "caper-sauce"
    walked = set()
    current = marrow
    while current is not None and current.parent is not None:
        assert current.ref.entry not in walked
        walked.add(current.ref.entry)
        current = catalogue.find(current.parent)


@pytest.mark.unit
def test_extract_records_the_file_line_of_every_heading():
    source = FakeSource(
        [
            "The basic sauces: Espagnole.",
            "22—BROWN SAUCE",
            "Reduce the wine.",
            "",
            "23—MADEIRA SAUCE",
            "Add espagnole.",
        ],
        line_offset=24,
    )
    catalogue = extract(source)
    first, second = catalogue.preparations
    assert first.ref.entry == 22
    # Body index 1, offset 24, so the heading is line 26 of the file.
    assert first.ref.line == 26
    assert second.ref.line == 29
    assert second.parent == "espagnole"
    assert first.parent is None


@pytest.mark.unit
def test_a_source_with_no_numbered_entries_is_an_error():
    with pytest.raises(NoPreparationsFound, match="no numbered entries"):
        extract(FakeSource(["plain prose", "and more of it"]))


@pytest.mark.unit
def test_a_source_whose_entries_are_never_sauces_is_an_error():
    with pytest.raises(NoPreparationsFound, match="none of them a sauce"):
        extract(FakeSource(["12—POTATOES BOILED", "in plain water"]))
