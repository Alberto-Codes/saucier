import json

import pytest

from saucier.adapters.driven.json_store import JsonCatalogueStore
from saucier.domain.errors import CatalogueUnwritable, SourceUnreadable
from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
from saucier.domain.types import ConceptId, Language


@pytest.fixture
def catalogue():
    return Catalogue(
        source_id="fixture",
        preparations=(
            Preparation(
                title="ORDINARY VELOUTÉ SAUCE",
                terms=(Term("ORDINARY VELOUTÉ SAUCE", Language.FRENCH),),
                body="Prose with an accent: réduction.",
                ref=SourceRef(source_id="fixture", entry=25, line=900),
                parent=ConceptId("espagnole"),
            ),
            # Most of the real catalogue looks like this one.
            Preparation(
                title="MARROW SAUCE",
                terms=(Term("MARROW SAUCE", Language.ENGLISH),),
                body="States no base.",
                ref=SourceRef(source_id="fixture", entry=26, line=950),
                parent=None,
            ),
        ),
        mothers=frozenset({ConceptId("espagnole")}),
    )


@pytest.mark.unit
def test_a_catalogue_survives_a_round_trip(tmp_path, catalogue):
    store = JsonCatalogueStore(directory=tmp_path)
    store.save(catalogue)
    assert store.load("fixture") == catalogue


@pytest.mark.unit
def test_save_reports_where_it_wrote(tmp_path, catalogue):
    written = JsonCatalogueStore(directory=tmp_path).save(catalogue)
    assert written == str(tmp_path / "fixture.json")


@pytest.mark.unit
def test_an_unresolved_parent_is_stored_as_null_not_a_word(tmp_path, catalogue):
    JsonCatalogueStore(directory=tmp_path).save(catalogue)
    payload = json.loads((tmp_path / "fixture.json").read_text(encoding="utf-8"))
    stored = {p["title"]: p["parent"] for p in payload["preparations"]}
    assert stored["MARROW SAUCE"] is None
    assert stored["ORDINARY VELOUTÉ SAUCE"] == "espagnole"


@pytest.mark.unit
def test_a_blank_parent_is_damage_not_an_absence_of_evidence(tmp_path, catalogue):
    path = tmp_path / "fixture.json"
    JsonCatalogueStore(directory=tmp_path).save(catalogue)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["preparations"][0]["parent"] = ""
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SourceUnreadable, match="damaged"):
        JsonCatalogueStore(directory=tmp_path).load("fixture")


@pytest.mark.unit
def test_accented_surfaces_are_stored_unescaped(tmp_path, catalogue):
    JsonCatalogueStore(directory=tmp_path).save(catalogue)
    written = (tmp_path / "fixture.json").read_text(encoding="utf-8")
    assert "VELOUTÉ" in written


@pytest.mark.unit
def test_loading_an_unknown_source_raises(tmp_path):
    with pytest.raises(SourceUnreadable, match="no catalogue stored"):
        JsonCatalogueStore(directory=tmp_path).load("absent")


@pytest.mark.unit
def test_a_truncated_file_is_reported_not_raised_raw(tmp_path):
    (tmp_path / "fixture.json").write_text('{"source_id": "fix', encoding="utf-8")
    with pytest.raises(SourceUnreadable, match="damaged"):
        JsonCatalogueStore(directory=tmp_path).load("fixture")


@pytest.mark.unit
def test_a_file_missing_a_key_is_reported_not_raised_raw(tmp_path):
    (tmp_path / "fixture.json").write_text('{"source_id": "fixture"}', encoding="utf-8")
    with pytest.raises(SourceUnreadable, match="damaged"):
        JsonCatalogueStore(directory=tmp_path).load("fixture")


@pytest.mark.unit
def test_a_save_leaves_no_temporary_file_behind(tmp_path, catalogue):
    JsonCatalogueStore(directory=tmp_path).save(catalogue)
    assert [p.name for p in tmp_path.iterdir()] == ["fixture.json"]


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
    (tmp_path / "fixture.json").mkdir()
    with pytest.raises(SourceUnreadable, match="cannot read catalogue"):
        JsonCatalogueStore(directory=tmp_path).load("fixture")
