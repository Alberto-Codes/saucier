import os

import pytest
from conftest import FIRST_PRINTING, REVISION, a_witness

from saucier.adapters.driven.json_store import JsonCatalogueStore
from saucier.adapters.driving import cli
from saucier.domain.errors import SourceUnreadable
from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
from saucier.domain.types import ConceptId, Language
from saucier.infrastructure.bootstrap import escoffier_sources

WITNESS = a_witness()


@pytest.fixture
def wired(monkeypatch, tmp_path):
    """Point the CLI at a temp data directory but the real corpus."""
    store = JsonCatalogueStore(directory=tmp_path)
    monkeypatch.setattr(cli, "catalogue_store", lambda: store)
    monkeypatch.setattr(cli, "escoffier_sources", escoffier_sources)
    return store


@pytest.mark.corpus
def test_parse_prints_the_census_it_just_computed(wired, capsys, census):
    assert cli.main(["parse"]) == 0
    out = capsys.readouterr().out
    assert (
        f"{census.sauces} sauces, {census.derived} derived, "
        f"{census.unresolved} unresolved"
    ) in out
    assert "mothers: bechamel, espagnole, hollandaise, tomato, veloute" in out


@pytest.mark.corpus
def test_parse_reports_the_edition_each_source_states(wired, capsys):
    assert cli.main(["parse"]) == 0
    out = capsys.readouterr().out
    assert (
        "escoffier-1909  New and Revised Edition, January 1909 "
        "(impression: January 1920)"
    ) in out
    assert "escoffier-1907  no edition stated, copyright 1907" in out
    assert "transcription of Project Gutenberg 71395" in out
    assert "ocr of Internet Archive cu31924000610117" in out


@pytest.mark.corpus
def test_parse_stores_every_witness_it_read(wired, capsys, first_printing_census):
    cli.main(["parse"])
    out = capsys.readouterr().out
    for source_id in (REVISION.source_id, FIRST_PRINTING.source_id):
        assert f"Wrote {os.path.relpath(wired.path_for(source_id))}" in out
    stored = wired.load(FIRST_PRINTING.source_id)
    assert len(stored.preparations) == first_printing_census.sauces
    assert stored.unresolved == first_printing_census.unresolved


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
def test_a_lookup_reads_the_witness_it_is_pointed_at(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["show", "aurore", "--source", FIRST_PRINTING.source_id]) == 0
    out = capsys.readouterr().out
    assert f"ocr of {FIRST_PRINTING.source_id}" in out


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
    assert "transcription of escoffier-1909" in out


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


@pytest.mark.corpus
def test_diff_reports_a_cause_on_every_row(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["diff", FIRST_PRINTING.source_id, REVISION.source_id]) == 0
    out = capsys.readouterr().out
    assert "escoffier-1907  ->  escoffier-1909" in out
    assert "ocr-suspected" in out
    assert "No row is adjudicated" in out


@pytest.mark.corpus
def test_diff_marks_aurore_as_a_disagreement_it_does_not_settle(wired, capsys):
    """The acceptance test: OCR removed a candidate and the refusal with it."""
    cli.main(["parse"])
    capsys.readouterr()
    cli.main(["diff", FIRST_PRINTING.source_id, REVISION.source_id])
    rows = [
        line
        for line in capsys.readouterr().out.splitlines()
        if line.strip().endswith("tomato / (none)") and " aurore-sauce " in line
    ]
    assert len(rows) == 1
    assert "parent-changed, ocr-suspected" in rows[0]
    assert "tomato / (none)" in rows[0]


@pytest.mark.corpus
def test_diff_reads_the_ocr_names_as_scan_artefacts_rather_than_removals(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    cli.main(["diff", FIRST_PRINTING.source_id, REVISION.source_id])
    out = capsys.readouterr().out
    assert "qenevoise-sauce ~ genevoise-sauce" in out
    assert "20 added, 12 parent-changed, 27 ocr-suspected" in out


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
            ref=SourceRef(
                source_id=WITNESS.source_id,
                entry=entry,
                line=entry,
                fidelity=WITNESS.fidelity,
            ),
            parent=ConceptId(parent),
        )

    catalogue = Catalogue(
        witness=WITNESS,
        preparations=(cyclic("A", "b", 1), cyclic("B", "a", 2)),
    )
    cli._print_children(catalogue, ConceptId("a"), prefix="", seen={ConceptId("a")})
    assert capsys.readouterr().out.count("B") == 1
