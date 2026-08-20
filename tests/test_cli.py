import os

import pytest

from saucier.adapters.driven.json_store import JsonCatalogueStore
from saucier.adapters.driving import cli
from saucier.domain.errors import SourceUnreadable
from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
from saucier.domain.types import ConceptId, Language
from saucier.infrastructure.bootstrap import escoffier_source
from saucier.infrastructure.config import ESCOFFIER


@pytest.fixture
def wired(monkeypatch, tmp_path):
    """Point the CLI at a temp data directory but the real corpus."""
    store = JsonCatalogueStore(directory=tmp_path)
    monkeypatch.setattr(cli, "catalogue_store", lambda: store)
    monkeypatch.setattr(cli, "escoffier_source", escoffier_source)
    return store


@pytest.mark.corpus
def test_parse_prints_the_census_it_just_computed(wired, capsys, census):
    assert cli.main(["parse"]) == 0
    out = capsys.readouterr().out
    assert f"sauces      {census.sauces}" in out
    assert f"derived     {census.derived} linked to a mother" in out
    assert f"unresolved  {census.unresolved} state no base in their prose" in out
    assert "mothers     bechamel, espagnole, hollandaise, tomato, veloute" in out


@pytest.mark.corpus
def test_parse_stores_what_it_printed(wired, capsys, census):
    cli.main(["parse"])
    written = os.path.relpath(wired.path_for(ESCOFFIER))
    assert f"Wrote {written}" in capsys.readouterr().out
    stored = wired.load(ESCOFFIER)
    assert len(stored.preparations) == census.sauces
    assert stored.unresolved == census.unresolved


@pytest.mark.corpus
def test_tree_prints_a_root_and_its_children(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["tree", "espagnole"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("BROWN SAUCE OR ESPAGNOLE  [espagnole]")
    assert "└──" in out or "├──" in out


@pytest.mark.corpus
def test_tree_heads_the_tree_with_the_concept_it_walked(wired, capsys):
    """The heading must name the root whose children follow it."""
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["tree", "hollandaise"]) == 0
    heading = capsys.readouterr().out.splitlines()[0]
    assert heading == "HOLLANDAISE SAUCE  [hollandaise]"


@pytest.mark.corpus
def test_tree_of_an_unknown_concept_fails_loudly(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["tree", "gravy-of-atlantis"]) == cli.NOT_FOUND
    assert "no preparation named" in capsys.readouterr().err


@pytest.mark.corpus
def test_show_prints_provenance_and_language(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["show", "bordelaise"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("SAUCE BORDELAISE")
    assert "[fr]" in out
    assert "(unresolved)" in out


@pytest.mark.corpus
def test_show_truncates_the_prose_and_says_so(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["show", "bordelaise", "--chars", "20"]) == 0
    assert "more characters, raise --chars" in capsys.readouterr().out


@pytest.mark.corpus
def test_show_of_an_unknown_concept_fails_loudly(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["show", "gravy-of-atlantis"]) == cli.NOT_FOUND


@pytest.mark.unit
def test_domain_errors_become_an_exit_code_not_a_traceback(monkeypatch, capsys):
    def boom():
        raise SourceUnreadable("corpus is missing")

    monkeypatch.setattr(cli, "catalogue_store", boom)
    assert cli.main(["tree", "espagnole"]) == cli.FAILED
    assert "corpus is missing" in capsys.readouterr().err


@pytest.mark.unit
def test_an_unfoldable_concept_is_an_exit_code_not_a_traceback(monkeypatch, capsys):
    monkeypatch.setattr(cli, "catalogue_store", lambda: None)
    assert cli.main(["show", "###"]) == cli.FAILED
    assert "empty concept id" in capsys.readouterr().err


@pytest.mark.unit
def test_the_parser_rejects_an_unknown_command():
    with pytest.raises(SystemExit):
        cli.main(["braise"])


@pytest.mark.corpus
def test_show_names_the_other_preparations_a_query_matches(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["show", "bordelaise"]) == 0
    assert "Also matching" in capsys.readouterr().err


@pytest.mark.corpus
def test_show_prints_the_whole_prose_when_it_fits(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["show", "brown-sauce", "--chars", "100000"]) == 0
    out = capsys.readouterr()
    assert "more characters" not in out.out
    assert "Also matching" not in out.err


@pytest.mark.unit
def test_a_cycle_in_the_recorded_parents_cannot_recurse_without_end(capsys):
    def cyclic(title, parent, entry):
        return Preparation(
            title=title,
            terms=(Term(title, Language.ENGLISH),),
            body="",
            ref=SourceRef(source_id="test", entry=entry, line=entry),
            parent=ConceptId(parent),
        )

    catalogue = Catalogue(
        source_id="test",
        preparations=(cyclic("A", "b", 1), cyclic("B", "a", 2)),
    )
    cli._print_children(catalogue, ConceptId("a"), prefix="", seen={ConceptId("a")})
    assert capsys.readouterr().out.count("B") == 1
