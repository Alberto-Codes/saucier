import pytest

from saucier.domain.errors import NoPreparationsFound
from saucier.domain.types import Language, to_concept_id
from saucier.services.extraction import (
    extract,
    find_mothers,
    is_sauce,
    iter_entries,
    names_a_sauce,
    resolve_parent,
    sauce_chapters,
    terms_in,
)

MOTHERS = frozenset(to_concept_id(m) for m in ["espagnole", "veloute", "bechamel"])


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
def test_two_bases_in_one_paragraph_resolve_to_nothing():
    body = "Boil one pint of fish velouté or, failing this, Béchamel sauce."
    assert resolve_parent(body, frozenset(), MOTHERS) is None


@pytest.mark.unit
def test_a_mother_must_appear_as_a_whole_word():
    mothers = frozenset({to_concept_id("tomato")})
    assert resolve_parent("Peel a pound of tomatoes.", frozenset(), mothers) is None


@pytest.mark.unit
def test_an_entry_with_no_prose_resolves_to_nothing():
    assert resolve_parent("", frozenset(), MOTHERS) is None


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
