import pytest

from saucier.domain.errors import SaucierError, UnfoldableTerm
from saucier.domain.types import Language, to_concept_id


@pytest.mark.unit
@pytest.mark.parametrize(
    ("surface", "expected"),
    [
        ("Velouté", "veloute"),
        ("VELOUTE", "veloute"),
        ("  Béchamel  ", "bechamel"),
        ("SAUCE BORDELAISE", "sauce-bordelaise"),
        ("Chaud-Froid", "chaud-froid"),
    ],
)
def test_folding_strips_diacritics_and_case(surface, expected):
    assert to_concept_id(surface) == expected


@pytest.mark.unit
def test_accented_and_unaccented_forms_share_one_concept():
    assert to_concept_id("Velouté") == to_concept_id("veloute")


@pytest.mark.unit
def test_empty_surface_is_an_error_not_an_empty_id():
    with pytest.raises(UnfoldableTerm, match="empty concept id"):
        to_concept_id("—  —")


@pytest.mark.unit
def test_an_unfoldable_term_is_a_domain_error_the_cli_can_catch():
    assert issubclass(UnfoldableTerm, SaucierError)
    assert issubclass(UnfoldableTerm, ValueError)


@pytest.mark.unit
def test_languages_are_iso_639_1():
    assert Language.FRENCH == "fr"
    assert Language.ENGLISH == "en"


@pytest.mark.unit
def test_only_languages_present_in_a_tracked_source_are_members():
    assert {m.value for m in Language} == {"en", "fr"}
