import pytest
from conftest import a_witness

from saucier.adapters.driven.normalised import (
    NormalisedText,
    normalise,
    repair_separator,
)
from saucier.domain.witness import Fidelity
from saucier.services.extraction import ENTRY

RAW = [
    "CHAPTER  I ",
    "The  basic  sauces :  Espagnole,  Veloute. ",
    "",
    "22—BROWN  SAUCE ",
]


class Scan:
    """A source that yields lines exactly as a scanner produced them."""

    witness = a_witness("book-1907", Fidelity.OCR)
    line_offset = 7

    def lines(self):
        return list(RAW)


@pytest.mark.unit
def test_double_spacing_collapses():
    assert normalise("CHAPTER  I ") == "CHAPTER I"


@pytest.mark.unit
def test_the_space_before_punctuation_goes():
    assert normalise("basic  sauces :  Espagnole") == "basic sauces: Espagnole"


@pytest.mark.unit
def test_normalisation_is_idempotent():
    once = [normalise(line) for line in RAW]
    assert [normalise(line) for line in once] == once


@pytest.mark.unit
def test_no_letter_is_repaired():
    """`velout^` stays `velout^`. Repair would manufacture agreement."""
    assert normalise("velout^  and  pur^e") == "velout^ and pur^e"


@pytest.mark.unit
def test_the_line_count_is_preserved_so_a_citation_still_lands():
    assert len(NormalisedText(inner=Scan()).lines()) == len(RAW)


@pytest.mark.unit
def test_identity_and_offset_come_from_the_wrapped_source():
    wrapped = NormalisedText(inner=Scan())
    assert wrapped.witness == Scan.witness
    assert wrapped.line_offset == 7


@pytest.mark.unit
def test_wrapping_twice_changes_nothing():
    once = NormalisedText(inner=Scan())
    assert NormalisedText(inner=once).lines() == once.lines()


@pytest.mark.unit
def test_a_broken_separator_is_mended():
    """`126-- MAYONNAISE SAUCE` is entry 126 of the same book."""
    assert repair_separator("126-- MAYONNAISE SAUCE") == "126—MAYONNAISE SAUCE"
    assert repair_separator("36 -DEVILLED SAUCE") == "36—DEVILLED SAUCE"


@pytest.mark.unit
def test_a_mended_line_is_one_the_extractor_can_read():
    """Nothing else couples the wrapper to the pattern it is repairing for."""
    assert ENTRY.match(repair_separator("126-- MAYONNAISE SAUCE"))


@pytest.mark.unit
def test_the_repair_leaves_the_title_exactly_as_the_scan_has_it():
    """`QRIBICHE` stays `QRIBICHE`. The comparison notices, not the reader."""
    assert repair_separator("125 -QRIBICHE SAUCE") == "125—QRIBICHE SAUCE"


@pytest.mark.unit
def test_numbered_prose_is_not_mistaken_for_a_heading():
    """The same book numbers its prose, and a sentence stays a sentence."""
    for line in (
        "1. Ordinary and clarified consommes.",
        "7. The basic sauces: Espagnole,- Veloute, Bechamel,",
        "12- The stock is then passed through a tammy.",
    ):
        assert repair_separator(line) == line


@pytest.mark.unit
def test_a_hyphenated_heading_is_still_mended():
    """`RED -HERRING BUTTER` is a heading whose title carries a hyphen."""
    assert repair_separator("286- RED -HERRING BUTTER") == "286—RED -HERRING BUTTER"


@pytest.mark.unit
def test_a_tail_of_marks_is_damage_rather_than_a_heading():
    assert repair_separator("1-^") == "1-^"
    assert repair_separator("430-A B") == "430-A B"


@pytest.mark.unit
def test_a_line_already_carrying_its_separator_is_left_alone():
    assert repair_separator("63—BEARNAISE SAUCE") == "63—BEARNAISE SAUCE"


@pytest.mark.unit
def test_the_repair_is_idempotent():
    once = repair_separator("126-- MAYONNAISE SAUCE")
    assert repair_separator(once) == once
