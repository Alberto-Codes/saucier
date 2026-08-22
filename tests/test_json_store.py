import json

import pytest

from saucier.adapters.driven.json_store import JsonCatalogueStore
from saucier.domain.errors import CatalogueUnwritable, SourceUnreadable
from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
from saucier.domain.types import ConceptId, Language
from saucier.domain.witness import Edition, Fidelity, Witness

WITNESS = Witness(
    work="fixture",
    origin="a test fixture",
    fidelity=Fidelity.TRANSCRIPTION,
    edition=Edition(
        statement="New and Revised Edition, January 1909",
        stated_year=1909,
        impression="January 1920",
        copyright_year=1907,
    ),
)
STORED = WITNESS.source_id


@pytest.fixture
def catalogue():
    return Catalogue(
        witness=WITNESS,
        preparations=(
            Preparation(
                title="ORDINARY VELOUTÉ SAUCE",
                terms=(Term("ORDINARY VELOUTÉ SAUCE", Language.FRENCH),),
                body="Prose with an accent: réduction.",
                ref=SourceRef(
                    source_id=STORED,
                    entry=25,
                    line=900,
                    fidelity=Fidelity.TRANSCRIPTION,
                ),
                parent=ConceptId("espagnole"),
            ),
            # Most of the real catalogue looks like this one.
            Preparation(
                title="MARROW SAUCE",
                terms=(Term("MARROW SAUCE", Language.ENGLISH),),
                body="States no base.",
                ref=SourceRef(
                    source_id=STORED,
                    entry=26,
                    line=950,
                    fidelity=Fidelity.TRANSCRIPTION,
                ),
                parent=None,
            ),
        ),
        mothers=frozenset({ConceptId("espagnole")}),
    )


@pytest.mark.unit
def test_a_catalogue_survives_a_round_trip(tmp_path, catalogue):
    store = JsonCatalogueStore(directory=tmp_path)
    store.save(catalogue)
    assert store.load(STORED) == catalogue


@pytest.mark.unit
def test_save_reports_where_it_wrote(tmp_path, catalogue):
    written = JsonCatalogueStore(directory=tmp_path).save(catalogue)
    assert written == str(tmp_path / f"{STORED}.json")


@pytest.mark.unit
def test_an_unresolved_parent_is_stored_as_null_not_a_word(tmp_path, catalogue):
    JsonCatalogueStore(directory=tmp_path).save(catalogue)
    payload = json.loads((tmp_path / f"{STORED}.json").read_text(encoding="utf-8"))
    stored = {p["title"]: p["parent"] for p in payload["preparations"]}
    assert stored["MARROW SAUCE"] is None
    assert stored["ORDINARY VELOUTÉ SAUCE"] == "espagnole"


@pytest.mark.unit
def test_a_blank_parent_is_damage_not_an_absence_of_evidence(tmp_path, catalogue):
    path = tmp_path / f"{STORED}.json"
    JsonCatalogueStore(directory=tmp_path).save(catalogue)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["preparations"][0]["parent"] = ""
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SourceUnreadable, match="damaged"):
        JsonCatalogueStore(directory=tmp_path).load(STORED)


@pytest.mark.unit
def test_accented_surfaces_are_stored_unescaped(tmp_path, catalogue):
    JsonCatalogueStore(directory=tmp_path).save(catalogue)
    written = (tmp_path / f"{STORED}.json").read_text(encoding="utf-8")
    assert "VELOUTÉ" in written


@pytest.mark.unit
def test_loading_an_unknown_source_raises(tmp_path):
    with pytest.raises(SourceUnreadable, match="no catalogue stored"):
        JsonCatalogueStore(directory=tmp_path).load("absent")


@pytest.mark.unit
def test_a_truncated_file_is_reported_not_raised_raw(tmp_path):
    (tmp_path / f"{STORED}.json").write_text('{"witness": {"work', encoding="utf-8")
    with pytest.raises(SourceUnreadable, match="damaged"):
        JsonCatalogueStore(directory=tmp_path).load(STORED)


@pytest.mark.unit
def test_a_file_missing_a_key_is_reported_not_raised_raw(tmp_path):
    (tmp_path / f"{STORED}.json").write_text('{"mothers": []}', encoding="utf-8")
    with pytest.raises(SourceUnreadable, match="damaged"):
        JsonCatalogueStore(directory=tmp_path).load(STORED)


@pytest.mark.unit
def test_a_save_leaves_no_temporary_file_behind(tmp_path, catalogue):
    JsonCatalogueStore(directory=tmp_path).save(catalogue)
    assert [p.name for p in tmp_path.iterdir()] == [f"{STORED}.json"]


@pytest.mark.unit
def test_a_source_id_cannot_escape_the_store(tmp_path):
    with pytest.raises(CatalogueUnwritable, match="plain file name"):
        JsonCatalogueStore(directory=tmp_path).load("../../escape")


@pytest.mark.unit
def test_a_write_failure_is_reported_as_a_domain_error(tmp_path, catalogue):
    blocked = tmp_path / "blocked"
    blocked.write_text("not a directory", encoding="utf-8")
    with pytest.raises(CatalogueUnwritable, match="cannot write catalogue"):
        JsonCatalogueStore(directory=blocked).save(catalogue)


@pytest.mark.unit
def test_a_catalogue_path_that_is_not_a_file_is_reported(tmp_path):
    (tmp_path / f"{STORED}.json").mkdir()
    with pytest.raises(SourceUnreadable, match="cannot read catalogue"):
        JsonCatalogueStore(directory=tmp_path).load(STORED)


@pytest.mark.unit
def test_the_stored_file_states_which_edition_it_holds(tmp_path, catalogue):
    JsonCatalogueStore(directory=tmp_path).save(catalogue)
    payload = json.loads((tmp_path / f"{STORED}.json").read_text(encoding="utf-8"))
    assert payload["witness"]["source_id"] == STORED
    assert payload["witness"]["fidelity"] == "transcription"
    assert payload["witness"]["origin"] == "a test fixture"
    assert payload["witness"]["edition"]["impression"] == "January 1920"


@pytest.mark.unit
def test_every_record_states_the_fidelity_of_the_text_it_came_through(
    tmp_path, catalogue
):
    JsonCatalogueStore(directory=tmp_path).save(catalogue)
    payload = json.loads((tmp_path / f"{STORED}.json").read_text(encoding="utf-8"))
    assert {p["ref"]["fidelity"] for p in payload["preparations"]} == {"transcription"}


@pytest.mark.unit
def test_an_unstated_edition_in_a_stored_file_is_damage(tmp_path, catalogue):
    path = tmp_path / f"{STORED}.json"
    JsonCatalogueStore(directory=tmp_path).save(catalogue)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["witness"]["edition"] |= {"stated_year": None, "copyright_year": None}
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SourceUnreadable, match="damaged"):
        JsonCatalogueStore(directory=tmp_path).load(STORED)
