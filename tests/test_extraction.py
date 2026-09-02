import pytest
from conftest import a_witness

from saucier.domain.errors import NoPreparationsFound
from saucier.domain.types import Language, to_concept_id
from saucier.services.extraction import (
    Candidate,
    continues_heading,
    extract,
    find_mothers,
    is_sauce,
    iter_entries,
    names_a_sauce,
    parent_candidates,
    resolve_parent,
    sauce_chapters,
    stated_candidates,
    terms_in,
)

MOTHERS = frozenset(to_concept_id(m) for m in ["espagnole", "veloute", "bechamel"])

CANDIDATES = {m: Candidate(m, m, mother=True) for m in MOTHERS}
"""Mothers alone, the smallest candidate set a source can declare."""


class FakeSource:
    """A source of the smallest shape the port accepts."""

    def __init__(self, lines, source_id="fixture-1900", line_offset=0):
        """Hold the lines a fake source hands back."""
        self._lines = lines
        self.witness = a_witness(source_id)
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
        # Inside a sauce chapter the chapter decides. The heading need not
        # name a mother, and need not say "sauce".
        ("LENTEN ESPAGNOLE", True, True),
        ("HALF GLAZE", True, True),
        ("BROWN ROUX", True, True),
        ("LOBSTER BUTTER", True, True),
        # Outside one, only the heading counts.
        ("LENTEN ESPAGNOLE", False, False),
        ("HALF GLAZE", False, False),
        ("TOMATO SALAD", False, False),
        ("GRILLED TOMATOES", False, False),
        ("VELOUTÉ AGNÈS SOREL", False, False),
        ("BROWN STOCK", False, False),
    ],
)
def test_the_heading_or_the_chapter_admits_an_entry(title, in_chapter, keep):
    assert is_sauce(title, in_chapter) is keep


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
def test_a_wrapped_heading_is_read_whole():
    """The typesetter breaks a long heading. Escoffier did not write two."""
    lines = [
        "63—BEARNAISE SAUCE WITH MEAT GLAZE, OTHERWISE VALOIS SAUCE OR FOYOT",
        "SAUCE",
        "",
        "Prepare it thus.",
    ]
    assert list(iter_entries(lines)) == [
        (
            63,
            0,
            "BEARNAISE SAUCE WITH MEAT GLAZE, OTHERWISE VALOIS SAUCE OR FOYOT SAUCE",
            "Prepare it thus.",
        )
    ]


@pytest.mark.unit
def test_a_heading_followed_by_prose_does_not_absorb_it():
    lines = ["22—BROWN SAUCE", "Reduce the wine until it thickens.", "", "More."]
    entries = list(iter_entries(lines))
    assert entries[0][2] == "BROWN SAUCE"
    assert entries[0][3].startswith("Reduce the wine")


@pytest.mark.unit
def test_a_heading_followed_by_shouted_prose_does_not_absorb_it():
    """Only the blank-line test stops this one. A paragraph runs on."""
    lines = ["22—BROWN SAUCE", "REDUCE THE WINE", "until it thickens.", ""]
    entries = list(iter_entries(lines))
    assert entries[0][2] == "BROWN SAUCE"
    assert entries[0][3].startswith("REDUCE THE WINE")


@pytest.mark.unit
def test_a_heading_followed_by_a_running_page_header_does_not_absorb_it():
    """`LEADING SAUCES 17` is page furniture, and it ends in its page number."""
    lines = ["22—BROWN SAUCE", "LEADING SAUCES 17", "", "Reduce the wine."]
    assert next(iter(iter_entries(lines)))[2] == "BROWN SAUCE"


@pytest.mark.unit
def test_a_heading_followed_by_the_next_index_line_does_not_absorb_it():
    """An index runs numbered titles together with no prose between them."""
    lines = ["1383—FRESH LEG OF PORK", "1384—FRESH PORK FILLETS", ""]
    assert [(n, title) for n, _, title, _ in iter_entries(lines)] == [
        (1383, "FRESH LEG OF PORK"),
        (1384, "FRESH PORK FILLETS"),
    ]


@pytest.mark.unit
def test_only_one_line_is_ever_joined():
    """A cap on what a wrong reading can absorb."""
    lines = ["22—BROWN SAUCE OR", "ESPAGNOLE", "", "AND MORE", "", "Reduce it."]
    _, _, title, body = next(iter(iter_entries(lines)))
    assert title == "BROWN SAUCE OR ESPAGNOLE"
    assert body.startswith("AND MORE")


@pytest.mark.unit
def test_a_line_carrying_no_letter_never_continues_a_heading():
    assert not continues_heading(["22—BROWN SAUCE", "* * *", ""], 1)


@pytest.mark.unit
def test_a_scanned_heading_whose_letters_became_digits_still_continues():
    """`CARD0N5, ETC.` carries no standalone number, so it is not furniture."""
    assert continues_heading(["1274—BLANQUETTE", "CARD0N5, ETC.", ""], 1)


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
def test_the_stated_candidates_are_named_in_the_order_the_paragraph_states_them():
    """`CARDINAL SAUCE` states Béchamel, then lobster butter. Neither wins."""
    candidates = dict(CANDIDATES)
    candidates[to_concept_id("lobster-butter")] = Candidate(
        149, to_concept_id("lobster-butter"), False
    )
    body = "Boil one pint of Béchamel. Finish it with three oz. of lobster butter."
    assert stated_candidates(body, frozenset(), candidates) == (
        "bechamel",
        "lobster-butter",
    )
    assert resolve_parent(body, frozenset(), candidates) is None
    # The later-declared candidate stated first comes first. Declaration
    # order is not statement order.
    reversed_body = "Melt three oz. of lobster butter. Add one pint of Béchamel."
    assert stated_candidates(reversed_body, frozenset(), candidates) == (
        "lobster-butter",
        "bechamel",
    )


@pytest.mark.unit
def test_a_mother_stated_after_its_entry_name_still_records_the_mother():
    """The mother concept wins however late the paragraph states it."""
    candidates = dict(CANDIDATES)
    candidates[to_concept_id("bechamel")] = Candidate(
        28, to_concept_id("bechamel"), mother=True
    )
    candidates[to_concept_id("white-sauce")] = Candidate(
        28, to_concept_id("white-sauce"), False
    )
    body = "Reduce the white sauce, then add more Béchamel."
    assert stated_candidates(body, frozenset(), candidates) == ("bechamel",)


@pytest.mark.unit
def test_two_names_reaching_one_preparation_are_one_stated_candidate():
    candidates = dict(CANDIDATES)
    candidates[to_concept_id("bechamel")] = Candidate(
        28, to_concept_id("bechamel"), mother=True
    )
    candidates[to_concept_id("bechamel-sauce")] = Candidate(
        28, to_concept_id("bechamel-sauce"), False
    )
    body = "Reduce the Béchamel sauce, then add more Béchamel."
    assert stated_candidates(body, frozenset(), candidates) == ("bechamel",)


@pytest.mark.unit
def test_a_paragraph_stating_nothing_has_no_stated_candidates():
    assert stated_candidates("Melt the butter.", frozenset(), CANDIDATES) == ()


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
    # The key is the heading's line, 5, not the entry number, 23.
    assert candidates[to_concept_id("madeira-sauce")] == Candidate(
        5, to_concept_id("madeira-sauce"), False
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
def test_the_chapter_admits_and_the_heading_admits_and_nothing_else_does():
    """One sauce chapter and one soup chapter, read end to end."""
    source = FakeSource(
        [
            "CHAPTER II",
            "",
            "THE LEADING WARM SAUCES",
            "",
            "19—BROWN ROUX",
            "Cook the flour in butter.",
            "",
            "22—BROWN SAUCE",
            "One lb. of brown roux in six quarts of stock.",
            "",
            "CHAPTER III",
            "",
            "SOUPS",
            "",
            "40—BROWN STOCK",
            "Bones and water.",
            "",
            "41—ONION SAUCE",
            "Mince the onion.",
        ]
    )
    catalogue = extract(source)
    assert [p.title for p in catalogue.preparations] == [
        "BROWN ROUX",
        "BROWN SAUCE",
        "ONION SAUCE",
    ]
    brown_sauce = catalogue.find(to_concept_id("brown-sauce"))
    assert brown_sauce is not None
    assert brown_sauce.parent == "brown-roux"


@pytest.mark.unit
def test_two_entries_the_scan_reads_as_one_number_keep_their_own_parents():
    """A scan can read `128` as `138`. The line, not the number, is identity."""
    source = FakeSource(
        [
            "22—BROWN SAUCE",
            "Reduce the wine.",
            "",
            "138—ONION SAUCE",
            "Add the brown sauce.",
            "",
            "138—CAPER SAUCE",
            "Pound the capers.",
        ]
    )
    brown, onion, caper = extract(source).preparations
    assert (onion.ref.entry, caper.ref.entry) == (138, 138)
    assert brown.parent is None
    assert onion.parent == "brown-sauce"
    assert caper.parent is None


@pytest.mark.unit
def test_a_source_with_no_numbered_entries_is_an_error():
    with pytest.raises(NoPreparationsFound, match="no numbered entries"):
        extract(FakeSource(["plain prose", "and more of it"]))


@pytest.mark.unit
def test_a_source_whose_entries_are_never_sauces_is_an_error():
    with pytest.raises(NoPreparationsFound, match="none of them a sauce"):
        extract(FakeSource(["12—POTATOES BOILED", "in plain water"]))


@pytest.mark.unit
def test_a_heading_on_the_last_line_of_a_source_has_nothing_to_join():
    assert not continues_heading(["22—BROWN SAUCE"], 1)
