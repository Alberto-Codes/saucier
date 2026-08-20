import pytest

from saucier.domain.errors import ProjectRootNotFound
from saucier.domain.models import Catalogue
from saucier.infrastructure.bootstrap import catalogue_store, escoffier_source
from saucier.infrastructure.config import ESCOFFIER, Paths


@pytest.mark.unit
def test_the_factories_honour_the_layout_they_are_given(tmp_path):
    paths = Paths(root=tmp_path)
    assert escoffier_source(paths).source_id == ESCOFFIER
    # Reached through the port, so the test binds to the contract.
    written = catalogue_store(paths).save(Catalogue(source_id=ESCOFFIER))
    assert written == str(tmp_path / "data" / f"{ESCOFFIER}.json")


@pytest.mark.unit
def test_discovery_finds_the_tree_holding_the_corpus():
    paths = Paths.discover()
    assert paths.corpus.is_dir()
    assert paths.escoffier.name == f"{ESCOFFIER}.txt"


@pytest.mark.unit
def test_discovery_reports_a_tree_with_no_corpus_rather_than_guessing(tmp_path):
    with pytest.raises(ProjectRootNotFound, match="no corpus/ directory"):
        Paths.discover(start=tmp_path / "nowhere" / "module.py")
