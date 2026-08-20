import pytest

from saucier.adapters.driven.json_store import JsonCatalogueStore
from saucier.adapters.driving import cli
from saucier.domain.errors import SourceUnreadable
from saucier.infrastructure.bootstrap import escoffier_source


@pytest.fixture
def wired(monkeypatch, tmp_path):
    """Point the CLI at a temp data directory but the real corpus."""
    store = JsonCatalogueStore(directory=tmp_path)
    monkeypatch.setattr(cli, "catalogue_store", lambda: store)
    monkeypatch.setattr(cli, "escoffier_source", escoffier_source)
    return store


@pytest.mark.corpus
def test_parse_reports_the_unresolved_count(wired, capsys):
    assert cli.main(["parse"]) == 0
    out = capsys.readouterr().out
    assert "unresolved" in out
    assert "mothers" in out


@pytest.mark.corpus
def test_tree_prints_a_root_and_its_children(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["tree", "espagnole"]) == 0
    out = capsys.readouterr().out
    assert "ESPAGNOLE" in out.upper()
    assert "└──" in out or "├──" in out


@pytest.mark.corpus
def test_tree_of_an_unknown_concept_fails_loudly(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["tree", "gravy-of-atlantis"]) == 1
    assert "no preparation named" in capsys.readouterr().err


@pytest.mark.corpus
def test_show_prints_provenance_and_language(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["show", "bordelaise"]) == 0
    out = capsys.readouterr().out
    assert "entry" in out and "line" in out
    assert "[fr]" in out


@pytest.mark.corpus
def test_show_of_an_unknown_concept_fails_loudly(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["show", "gravy-of-atlantis"]) == 1


@pytest.mark.unit
def test_domain_errors_become_an_exit_code_not_a_traceback(monkeypatch, capsys):
    def boom():
        raise SourceUnreadable("corpus is missing")

    monkeypatch.setattr(cli, "catalogue_store", boom)
    assert cli.main(["tree", "espagnole"]) == 2
    assert "corpus is missing" in capsys.readouterr().err


@pytest.mark.unit
def test_the_parser_rejects_an_unknown_command():
    with pytest.raises(SystemExit):
        cli.main(["braise"])
