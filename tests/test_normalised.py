import pytest
from conftest import a_witness

from saucier.adapters.driven.normalised import NormalisedText, normalise
from saucier.domain.witness import Fidelity

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
