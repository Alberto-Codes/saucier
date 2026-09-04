import pytest
from conftest import a_witness

from saucier.domain.errors import ProjectRootNotFound
from saucier.domain.models import Catalogue
from saucier.domain.witness import Fidelity
from saucier.infrastructure.bootstrap import (
    catalogue_interchange,
    catalogue_store,
    default_source_id,
    escoffier_sources,
)
from saucier.infrastructure.config import SCAN_FILE, TRANSCRIPTION_FILE, Paths


@pytest.mark.unit
def test_the_factories_honour_the_layout_they_are_given(tmp_path):
    witness = a_witness()
    # Reached through the port, so the test binds to the contract.
    written = catalogue_store(Paths(root=tmp_path)).save(Catalogue(witness=witness))
    assert written == str(tmp_path / "data" / f"{witness.source_id}.json")


@pytest.mark.corpus
def test_the_corpus_holds_two_witnesses_of_one_work():
    revision, first = escoffier_sources()
    assert revision.witness.source_id == "escoffier-1909"
    assert revision.witness.fidelity == Fidelity.TRANSCRIPTION
    assert first.witness.source_id == "escoffier-1907"
    assert first.witness.fidelity == Fidelity.OCR


@pytest.mark.corpus
def test_the_scanned_witness_is_wired_through_the_normalising_wrapper():
    """A reader sees which source is cleaned, at the assembly root."""
    assert "  " not in escoffier_sources()[1].lines()[0]


@pytest.mark.corpus
def test_a_lookup_defaults_to_the_revision():
    assert default_source_id() == "escoffier-1909"


@pytest.mark.unit
def test_discovery_finds_the_tree_holding_the_corpus():
    paths = Paths.discover()
    assert paths.corpus.is_dir()
    assert paths.escoffier_transcription.name == TRANSCRIPTION_FILE
    assert paths.escoffier_scan.name == SCAN_FILE


@pytest.mark.unit
def test_discovery_reports_a_tree_with_no_corpus_rather_than_guessing(tmp_path):
    with pytest.raises(ProjectRootNotFound, match="no corpus/ directory"):
        Paths.discover(start=tmp_path / "nowhere" / "module.py")


@pytest.mark.unit
def test_the_interchange_factory_returns_a_working_codec():
    witness = a_witness()
    catalogue = Catalogue(witness=witness)
    interchange = catalogue_interchange()
    assert interchange.decode(interchange.encode([catalogue])) == (catalogue,)
