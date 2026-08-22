import pytest

from saucier.domain.errors import EditionUnstated
from saucier.domain.witness import Edition, Fidelity, Witness


def edition(statement=None, stated_year=None, impression=None, copyright_year=1907):
    return Edition(
        statement=statement,
        stated_year=stated_year,
        impression=impression,
        copyright_year=copyright_year,
    )


@pytest.mark.unit
def test_a_stated_edition_decides_the_year():
    revised = edition(
        statement="New and Revised Edition, January 1909",
        stated_year=1909,
        impression="January 1920",
    )
    assert revised.year == 1909
    assert revised.stated


@pytest.mark.unit
def test_a_text_stating_no_edition_falls_back_to_its_copyright_year():
    first = edition()
    assert first.year == 1907
    assert not first.stated


@pytest.mark.unit
def test_an_edition_with_no_year_at_all_is_reported_not_guessed():
    with pytest.raises(EditionUnstated, match="neither an edition year"):
        edition(copyright_year=None)


@pytest.mark.unit
def test_a_source_id_is_the_work_and_the_year_it_read():
    witness = Witness(
        work="escoffier",
        origin="Project Gutenberg 71395",
        fidelity=Fidelity.TRANSCRIPTION,
        edition=edition(
            statement="New and Revised Edition, January 1909", stated_year=1909
        ),
    )
    assert witness.source_id == "escoffier-1909"


@pytest.mark.unit
def test_a_witness_that_cannot_name_itself_is_rejected():
    with pytest.raises(ValueError, match="needs a work and an origin"):
        Witness(
            work=" ",
            origin="somewhere",
            fidelity=Fidelity.OCR,
            edition=edition(),
        )
    with pytest.raises(ValueError, match="needs a work and an origin"):
        Witness(
            work="escoffier",
            origin="",
            fidelity=Fidelity.OCR,
            edition=edition(),
        )
