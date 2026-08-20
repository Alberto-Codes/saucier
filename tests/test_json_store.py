import pytest

from saucier.adapters.driven.json_store import JsonCatalogueStore
from saucier.domain.errors import SourceUnreadable
from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
from saucier.domain.types import ConceptId, Language


@pytest.fixture
def catalogue():
    return Catalogue(
        source_id="fixture",
        preparations=(
            Preparation(
                title="ORDINARY VELOUTÉ SAUCE",
                terms=(Term.of("ORDINARY VELOUTÉ SAUCE", Language.FRENCH),),
                body="Prose with an accent: réduction.",
                ref=SourceRef("fixture", 25, 900),
                parent=ConceptId("espagnole"),
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
def test_accented_surfaces_are_stored_unescaped(tmp_path, catalogue):
    JsonCatalogueStore(directory=tmp_path).save(catalogue)
    written = (tmp_path / "fixture.json").read_text(encoding="utf-8")
    assert "VELOUTÉ" in written


@pytest.mark.unit
def test_loading_an_unknown_source_raises(tmp_path):
    with pytest.raises(SourceUnreadable, match="no catalogue stored"):
        JsonCatalogueStore(directory=tmp_path).load("absent")
