import pytest
from conftest import a_witness

from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
from saucier.domain.types import ConceptId, Language
from saucier.domain.witness import Fidelity
from saucier.services.comparison import Cause, compare

SCAN = a_witness("book-1907", Fidelity.OCR)
CLEAN = a_witness("book-1909", Fidelity.TRANSCRIPTION)


def catalogue(witness, entries):
    """Build a catalogue from (title, parent) pairs."""
    return Catalogue(
        witness=witness,
        preparations=tuple(
            Preparation(
                title=title,
                terms=(Term(title, Language.ENGLISH),),
                body="",
                ref=SourceRef(
                    source_id=witness.source_id,
                    entry=number,
                    line=number,
                    fidelity=witness.fidelity,
                ),
                parent=ConceptId(parent) if parent else None,
            )
            for number, (title, parent) in enumerate(entries, start=1)
        ),
    )


def causes_for(report, concept):
    rows = [*report.presence, *report.parents]
    return next(row.causes for row in rows if row.concept == concept)


@pytest.mark.unit
def test_a_name_only_the_later_witness_holds_is_added():
    report = compare(
        catalogue(SCAN, [("BROWN SAUCE", None)]),
        catalogue(CLEAN, [("BROWN SAUCE", None), ("APPLE SAUCE", None)]),
    )
    assert causes_for(report, "apple-sauce") == (Cause.ADDED,)


@pytest.mark.unit
def test_a_name_only_the_earlier_witness_holds_is_removed():
    report = compare(
        catalogue(SCAN, [("BROWN SAUCE", None), ("LOST SAUCE", None)]),
        catalogue(CLEAN, [("BROWN SAUCE", None)]),
    )
    assert causes_for(report, "lost-sauce") == (Cause.REMOVED,)


@pytest.mark.unit
def test_a_name_mangled_inside_its_words_is_ocr_suspected_rather_than_removed():
    """All fourteen 1907-only concepts are this shape."""
    report = compare(
        catalogue(SCAN, [("QENEVOISE SAUCE", None)]),
        catalogue(CLEAN, [("GENEVOISE SAUCE", None)]),
    )
    assert causes_for(report, "qenevoise-sauce") == (Cause.OCR_SUSPECTED,)
    assert len(report.presence) == 1


@pytest.mark.unit
def test_a_heading_that_gained_whole_words_is_a_retitle_between_clean_texts():
    other = a_witness("book-1912", Fidelity.TRANSCRIPTION)
    report = compare(
        catalogue(CLEAN, [("BEARNAISE SAUCE WITH MEAT GLAZE", None)]),
        catalogue(
            other, [("BEARNAISE SAUCE WITH MEAT GLAZE, OTHERWISE VALOIS SAUCE", None)]
        ),
    )
    row = report.presence[0]
    assert row.causes == (Cause.RETITLED,)
    assert row.counterpart == "bearnaise-sauce-with-meat-glaze-otherwise-valois-sauce"


@pytest.mark.unit
def test_a_gained_heading_against_a_scan_carries_both_causes_and_settles_none():
    """A scan can drop a heading's tail, so neither reading is ruled out."""
    report = compare(
        catalogue(SCAN, [("BEARNAISE SAUCE WITH MEAT GLAZE", None)]),
        catalogue(
            CLEAN, [("BEARNAISE SAUCE WITH MEAT GLAZE, OTHERWISE VALOIS SAUCE", None)]
        ),
    )
    row = report.presence[0]
    assert row.causes == (Cause.RETITLED, Cause.OCR_SUSPECTED)
    assert "cannot say which" in row.note


@pytest.mark.unit
def test_a_short_run_inside_a_long_name_is_not_read_as_a_retitle():
    report = compare(
        catalogue(SCAN, [("PLAIN SAUCE", None)]),
        catalogue(CLEAN, [("A VERY LONG AND PLAIN SAUCE OF SOME KIND", None)]),
    )
    assert {row.causes for row in report.presence} == {
        (Cause.ADDED,),
        (Cause.REMOVED,),
    }


@pytest.mark.unit
def test_a_parent_disagreement_is_reported_and_never_adjudicated():
    """`AURORE SAUCE` states two candidates in one witness and one in the other."""
    report = compare(
        catalogue(SCAN, [("AURORE SAUCE", "tomato"), ("TOMATO SAUCE", None)]),
        catalogue(CLEAN, [("AURORE SAUCE", None), ("TOMATO SAUCE", None)]),
    )
    row = report.parents[0]
    assert row.concept == "aurore-sauce"
    assert row.causes == (Cause.PARENT_CHANGED, Cause.OCR_SUSPECTED)
    assert (row.older, row.newer) == ("tomato", None)


@pytest.mark.unit
def test_two_proofread_witnesses_leave_a_disagreement_unqualified():
    other = a_witness("book-1912", Fidelity.TRANSCRIPTION)
    report = compare(
        catalogue(CLEAN, [("AURORE SAUCE", "tomato")]),
        catalogue(other, [("AURORE SAUCE", None)]),
    )
    assert report.parents[0].causes == (Cause.PARENT_CHANGED,)
    assert not report.scanned


@pytest.mark.unit
def test_no_pairing_is_attempted_between_two_proofread_witnesses():
    """A character difference between proofread texts is not a scan artefact."""
    other = a_witness("book-1912", Fidelity.TRANSCRIPTION)
    report = compare(
        catalogue(CLEAN, [("GENEVOISE SAUCE", None)]),
        catalogue(other, [("GENEVOIZE SAUCE", None)]),
    )
    assert {row.causes for row in report.presence} == {
        (Cause.ADDED,),
        (Cause.REMOVED,),
    }


@pytest.mark.unit
def test_every_row_carries_a_cause():
    report = compare(
        catalogue(SCAN, [("QENEVOISE SAUCE", None), ("LOST SAUCE", "x-sauce")]),
        catalogue(CLEAN, [("GENEVOISE SAUCE", None), ("APPLE SAUCE", None)]),
    )
    assert all(row.causes for row in (*report.presence, *report.parents))


@pytest.mark.unit
def test_the_tally_counts_a_row_under_each_cause_it_carries():
    report = compare(
        catalogue(SCAN, [("AURORE SAUCE", "tomato"), ("TOMATO SAUCE", None)]),
        catalogue(CLEAN, [("AURORE SAUCE", None), ("TOMATO SAUCE", None)]),
    )
    assert report.tally() == {Cause.PARENT_CHANGED: 1, Cause.OCR_SUSPECTED: 1}


@pytest.mark.unit
def test_a_paired_name_still_has_its_derivation_compared():
    """Pairing must not hide a parent disagreement it created the names for."""
    report = compare(
        catalogue(SCAN, [("QENEVOISE SAUCE", None)]),
        catalogue(CLEAN, [("GENEVOISE SAUCE", "espagnole")]),
    )
    row = report.parents[0]
    assert row.concept == "qenevoise-sauce"
    assert row.counterpart == "genevoise-sauce"
    assert (row.older, row.newer) == (None, "espagnole")


@pytest.mark.unit
def test_a_parent_named_under_two_spellings_is_not_a_change():
    """The pairing may not manufacture a finding out of its own matching."""
    report = compare(
        catalogue(SCAN, [("RAVIQOTE SAUCE", None), ("CHILD SAUCE", "raviqote-sauce")]),
        catalogue(CLEAN, [("RAVIGOTE SAUCE", None), ("CHILD SAUCE", "ravigote-sauce")]),
    )
    assert report.parents == ()


@pytest.mark.unit
def test_an_unpaired_row_never_claims_a_test_that_was_not_run():
    """Two proofread witnesses are never scored against each other."""
    other = a_witness("book-1912", Fidelity.TRANSCRIPTION)
    report = compare(
        catalogue(CLEAN, [("GENEVOISE SAUCE", None)]),
        catalogue(other, [("GENEVOIZE SAUCE", None)]),
    )
    assert all("no witness is ocr" in row.note for row in report.presence)


@pytest.mark.unit
def test_a_name_that_lost_a_pairing_reports_the_resemblance_it_had():
    """It resembles something. Saying otherwise is a false claim."""
    report = compare(
        catalogue(SCAN, [("QENEVOISE SAUCE", None)]),
        catalogue(CLEAN, [("GENEVOISE SAUCE", None), ("GENEVOISF SAUCE", None)]),
    )
    lost = [row for row in report.presence if row.causes == (Cause.ADDED,)]
    assert len(lost) == 1
    assert "pairs better elsewhere" in lost[0].note
