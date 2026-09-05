import io
import json
import os
import sys
from fractions import Fraction

import pytest
from conftest import FIRST_PRINTING, REVISION, a_witness

from saucier.adapters.driven.json_store import JsonCatalogueStore
from saucier.adapters.driving import cli
from saucier.domain.errors import SourceUnreadable
from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
from saucier.domain.procedure import Input, Operation, Parameter, Procedure
from saucier.domain.types import ConceptId, Language
from saucier.infrastructure.bootstrap import escoffier_sources
from saucier.services.extraction import extract

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
    assert "parent  half-glaze" in out
    assert "transcription of escoffier-1909" in out


@pytest.mark.corpus
def test_show_names_the_candidates_an_unresolved_parent_states(wired, capsys):
    """The acceptance test for ADR-0015's loss. Cardinal states both names."""
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["show", "cardinal-sauce"]) == 0
    out = capsys.readouterr().out
    assert "  parent  (unresolved)\n  stated  bechamel, lobster-butter\n" in out
    assert cli.main(["show", "aurore-sauce"]) == 0
    out = capsys.readouterr().out
    assert "  parent  (unresolved)\n  stated  veloute, tomato\n" in out


@pytest.mark.corpus
def test_show_prints_the_recorded_procedure_one_operation_per_line(wired, capsys):
    """The acceptance test for ADR-0017. Every word is the entry's own."""
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["show", "mornay"]) == 0
    out = capsys.readouterr().out
    assert "  parent  bechamel\n  procedure  6 operations, recorded by hand\n" in out
    assert "    Boil      Béchamel Sauce [fr] 1 pint, fumet [fr] 1/4 pint\n" in out
    assert "    Reduce    criterion: by a good quarter (unresolved)\n" in out
    assert (
        "    Put       duration: a few minutes (unresolved), on the fire again\n" in out
    )
    assert (
        "    Finish    butter [en] 2 oz., away from the fire, added by degrees\n" in out
    )


@pytest.mark.corpus
def test_show_reads_the_scan_procedure_under_its_damaged_name(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["show", "mornay", "--source", FIRST_PRINTING.source_id]) == (
        cli.NOT_FOUND
    )
    capsys.readouterr()
    assert (
        cli.main(["show", "morn-ay-sauce", "--source", FIRST_PRINTING.source_id]) == 0
    )
    out = capsys.readouterr().out
    assert "  parent  (unresolved)\n  stated  no candidate\n" in out
    assert "  procedure  6 operations, recorded by hand\n" in out
    assert "    Boil      Bdchamel Sauce [fr] 1 pint, fumet [fr] 1/4 pint\n" in out


@pytest.mark.corpus
def test_show_says_when_no_procedure_is_recorded(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["show", "bordelaise"]) == 0
    assert (
        "  parent  half-glaze\n  procedure  (unrecorded)\n" in capsys.readouterr().out
    )


@pytest.mark.corpus
def test_show_says_when_an_unresolved_parent_states_no_candidate(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["show", "brown-roux"]) == 0
    out = capsys.readouterr().out
    assert "  parent  (unresolved)\n  stated  no candidate\n" in out


@pytest.mark.corpus
def test_tree_prints_half_glaze_between_espagnole_and_robert(wired, capsys):
    """The three-link chain the book wrote, with the roux above it."""
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["tree", "espagnole"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == (
        "BROWN SAUCE OR ESPAGNOLE  [espagnole]  derives from brown-roux"
    )
    assert lines[1] == "├── HALF GLAZE  (en)"
    robert = [n for n, line in enumerate(lines) if line.endswith("ROBERT SAUCE  (en)")]
    assert len(robert) == 1
    assert lines[robert[0]].startswith("│   ")
    assert robert[0] > 1


@pytest.mark.corpus
def test_tree_of_a_root_with_no_parent_keeps_the_bare_heading(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["tree", "brown-roux"]) == 0
    assert capsys.readouterr().out.splitlines()[0] == "BROWN ROUX  [brown-roux]"


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
    assert "11 unmatched, 19 parent-changed, 36 ocr-suspected" in out


@pytest.mark.corpus
def test_diff_prints_the_blind_spot_beside_the_counts(wired, capsys):
    """A reader may not see the counts without seeing what was unread."""
    cli.main(["parse"])
    capsys.readouterr()
    cli.main(["diff", FIRST_PRINTING.source_id, REVISION.source_id])
    out = capsys.readouterr().out
    assert (
        "entries read  2679 of escoffier-1907, 2963 of escoffier-1909, "
        "a blind spot of 284"
    ) in out
    assert "never that the printing lacks one" in out


@pytest.mark.corpus
def test_diff_claims_no_addition_against_a_scanned_witness(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    cli.main(["diff", FIRST_PRINTING.source_id, REVISION.source_id])
    out = capsys.readouterr().out
    assert " added " not in out
    assert " removed " not in out


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


def a_stored_catalogue(store):
    """Extract a four-entry source into a store, so the CLI reads it back.

    A sauce chapter with a roux, a mother that states the roux, a sauce that
    states the mother and a butter, and a butter. The declared mother
    `tomato` has no entry of its own.
    """

    class Source:
        line_offset = 0

        def __init__(self):
            self.witness = a_witness("book-1909")

        def lines(self):
            return [
                "The basic sauces: Espagnole and Tomato.",
                "CHAPTER II",
                "",
                "THE LEADING WARM SAUCES",
                "",
                "19—BROWN ROUX",
                "Cook the flour in butter.",
                "",
                "22—ESPAGNOLE",
                "One lb. of brown roux in stock.",
                "",
                "69—CARDINAL SAUCE",
                "Boil the espagnole. Finish with lobster butter.",
                "",
                "149—LOBSTER BUTTER",
                "Pound the shells.",
            ]

    store.save(extract(Source()))
    return store


@pytest.fixture
def small(monkeypatch, tmp_path):
    """The CLI wired to a four-entry catalogue, with no corpus read."""
    store = a_stored_catalogue(JsonCatalogueStore(directory=tmp_path))
    monkeypatch.setattr(cli, "catalogue_store", lambda: store)
    monkeypatch.setattr(cli, "default_source_id", lambda: "book-1909")
    return store


@pytest.mark.unit
def test_show_prints_every_stated_candidate_in_statement_order(small, capsys):
    assert cli.main(["show", "cardinal-sauce"]) == 0
    assert "  parent  (unresolved)\n  stated  espagnole, lobster-butter\n" in (
        capsys.readouterr().out
    )


@pytest.mark.unit
def test_show_prints_no_candidate_when_the_paragraph_states_none(small, capsys):
    assert cli.main(["show", "brown-roux"]) == 0
    assert "  parent  (unresolved)\n  stated  no candidate\n" in capsys.readouterr().out


@pytest.mark.unit
def test_show_prints_a_resolved_parent_with_no_stated_line(small, capsys):
    assert cli.main(["show", "espagnole"]) == 0
    out = capsys.readouterr().out
    assert "  parent  brown-roux\n" in out
    assert "stated" not in out


@pytest.mark.unit
def test_show_prints_unrecorded_for_a_catalogue_with_no_procedure(small, capsys):
    assert cli.main(["show", "espagnole"]) == 0
    assert (
        "  parent  brown-roux\n  procedure  (unrecorded)\n" in capsys.readouterr().out
    )


@pytest.mark.unit
def test_a_recorded_procedure_the_body_does_not_state_is_an_exit_code(
    small, monkeypatch, capsys
):
    """A hand can misquote. The command reports it rather than printing it."""

    class Misquoting:
        recorder = "test"

        def at(self, ref):
            return Procedure(
                (
                    Operation(
                        wording="Strain the moon",
                        verb=Term("Strain", Language.ENGLISH),
                        inputs=(),
                        instrument=None,
                        criterion=None,
                        duration=None,
                        constraints=(),
                    ),
                )
            )

    monkeypatch.setattr(cli, "recorded_procedures", Misquoting)
    assert cli.main(["show", "espagnole"]) == cli.FAILED
    out, err = capsys.readouterr()
    assert "does not state 'Strain the moon'" in err
    assert out == ""


@pytest.mark.unit
def test_tree_heading_names_the_root_own_parent(small, capsys):
    assert cli.main(["tree", "espagnole"]) == 0
    # Cardinal states two candidates, so nothing hangs beneath Espagnole.
    lines = capsys.readouterr().out.splitlines()
    assert lines == ["ESPAGNOLE  [espagnole]  derives from brown-roux"]


@pytest.mark.unit
def test_tree_heading_of_a_root_with_no_parent_is_bare(small, capsys):
    assert cli.main(["tree", "brown-roux"]) == 0
    assert capsys.readouterr().out.splitlines()[0] == "BROWN ROUX  [brown-roux]"


@pytest.mark.unit
def test_tree_of_a_declared_mother_with_no_entry_prints_the_concept(small, capsys):
    """`tomato` is a mother the source names and never numbers."""
    assert cli.main(["tree", "tomato"]) == 0
    assert capsys.readouterr().out.splitlines()[0] == "tomato  [tomato]"


@pytest.mark.unit
def test_an_operation_line_renders_what_the_clause_states_and_nothing_else():
    """An input with no quantity, and a number with no unit, print bare."""
    season = Operation(
        wording="Season with salt, the yolks of three eggs, and a pinch",
        verb=Term("Season", Language.ENGLISH),
        inputs=(
            Input(wording="salt", term=Term("salt", Language.ENGLISH), quantity=None),
            Input(
                wording="the yolks of three eggs",
                term=Term("eggs", Language.ENGLISH),
                quantity=Parameter(wording="three", number=Fraction(3), unit=None),
            ),
        ),
        instrument=None,
        criterion=None,
        duration=None,
        constraints=(),
    )
    strain = Operation(
        wording="Strain",
        verb=Term("Strain", Language.ENGLISH),
        inputs=(),
        instrument=None,
        criterion=None,
        duration=None,
        constraints=(),
    )
    assert cli._operation_lines(Procedure((season, strain))) == [
        "    Season  salt [en], eggs [en] 3",
        "    Strain",
    ]


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


@pytest.mark.unit
def test_a_catalogue_with_no_entry_count_says_the_blind_spot_is_unknown(
    monkeypatch, tmp_path, capsys
):
    """An older stored file recorded no count, and unknown is not zero."""
    store = JsonCatalogueStore(directory=tmp_path)
    monkeypatch.setattr(cli, "catalogue_store", lambda: store)
    for witness in (a_witness("book-1907"), a_witness("book-1909")):
        store.save(Catalogue(witness=witness))
    assert cli.main(["diff", "book-1907", "book-1909"]) == 0
    out = capsys.readouterr().out
    assert "entries read  not recorded, so the blind spot is unknown" in out


@pytest.mark.unit
def test_two_proofread_witnesses_get_the_blind_spot_without_the_caveat(
    monkeypatch, tmp_path, capsys
):
    """The caveat belongs to damage. The measurement belongs to every diff."""
    store = JsonCatalogueStore(directory=tmp_path)
    monkeypatch.setattr(cli, "catalogue_store", lambda: store)
    for source_id, count in (("book-1907", 2900), ("book-1909", 2963)):
        store.save(Catalogue(witness=a_witness(source_id), entries_read=count))
    assert cli.main(["diff", "book-1907", "book-1909"]) == 0
    out = capsys.readouterr().out
    assert "a blind spot of 63" in out
    assert "never that the printing lacks one" not in out


# --------------------------------------------------------------------------- #
# The interchange round trip
# --------------------------------------------------------------------------- #


@pytest.mark.corpus
def test_export_writes_only_records_to_stdout(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    assert cli.main(["export"]) == 0
    out, err = capsys.readouterr()
    assert err == ""
    lines = out.splitlines()
    assert len(lines) == 2 + 151 + 140
    assert out.endswith("\n") and not out.endswith("\n\n")
    kinds = [json.loads(line)["type"] for line in lines]
    assert kinds[:2] == ["catalogue", "catalogue"]
    assert set(kinds[2:]) == {"preparation"}


@pytest.mark.corpus
def test_export_writes_the_catalogues_in_the_configured_order(wired, capsys):
    cli.main(["parse"])
    capsys.readouterr()
    cli.main(["export"])
    heads = [json.loads(line) for line in capsys.readouterr().out.splitlines()[:2]]
    assert [h["id"] for h in heads] == [REVISION.source_id, FIRST_PRINTING.source_id]


@pytest.mark.corpus
def test_export_before_parse_fails_on_stderr_and_keeps_stdout_empty(wired, capsys):
    assert cli.main(["export"]) == cli.FAILED
    out, err = capsys.readouterr()
    assert out == ""
    assert "no catalogue stored" in err
    assert "Run `saucier parse`" in err


@pytest.mark.corpus
def test_the_shell_round_trip_reproduces_the_census(
    wired, capsys, monkeypatch, census, first_printing_census
):
    cli.main(["parse"])
    capsys.readouterr()
    cli.main(["export"])
    exported = capsys.readouterr().out
    monkeypatch.setattr(sys, "stdin", io.StringIO(exported))
    assert cli.main(["import", "--check"]) == 0
    out, err = capsys.readouterr()
    assert err == ""
    first = (
        f"{census.source_id:<14}  {census.sauces} sauces, "
        f"{census.derived} derived, {census.unresolved} unresolved"
    )
    second = (
        f"{first_printing_census.source_id:<14}  {first_printing_census.sauces} "
        f"sauces, {first_printing_census.derived} derived, "
        f"{first_printing_census.unresolved} unresolved"
    )
    assert out.splitlines()[:2] == [first, second]
    assert (
        out.splitlines()[2]
        == "2 catalogues and 291 preparations rebuilt. Nothing written."
    )


@pytest.mark.corpus
def test_import_check_touches_neither_the_store_nor_the_disk(
    wired, capsys, monkeypatch, tmp_path
):
    cli.main(["parse"])
    capsys.readouterr()
    cli.main(["export"])
    exported = capsys.readouterr().out
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    monkeypatch.setattr(
        cli, "catalogue_store", lambda: pytest.fail("import reached for the store")
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(exported))
    assert cli.main(["import", "--check"]) == 0
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


@pytest.mark.unit
def test_import_of_only_blank_lines_fails_like_an_empty_stream(capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("\n\n   \n"))
    assert cli.main(["import", "--check"]) == cli.FAILED
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "saucier: interchange carries no catalogues\n"


@pytest.mark.corpus
def test_export_writes_utf8_whatever_the_stream_was_told(wired, capsys, monkeypatch):
    """The corpus holds 144 em dashes. A latin-1 stdout must not get to refuse one."""
    cli.main(["parse"])
    capsys.readouterr()
    sink = io.TextIOWrapper(io.BytesIO(), encoding="latin-1", newline="\n")
    monkeypatch.setattr(sys, "stdout", sink)
    assert cli.main(["export"]) == 0
    raw = sink.buffer.getvalue()
    assert "—".encode() in raw
    assert raw.decode("utf-8").count("\n") == 2 + 151 + 140


@pytest.mark.unit
def test_import_reads_utf8_strictly_and_names_the_bad_line(capsys, monkeypatch):
    raw = b'\n{"body":"\xff"}\n'
    monkeypatch.setattr(
        sys, "stdin", io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8")
    )
    assert cli.main(["import", "--check"]) == cli.FAILED
    out, err = capsys.readouterr()
    assert out == ""
    assert (
        err == "saucier: line 2: not UTF-8 (invalid start byte at byte 9 of the line)\n"
    )


@pytest.mark.corpus
def test_a_stream_cut_after_the_catalogue_records_is_refused(
    wired, capsys, monkeypatch
):
    """`saucier export | head -n 2 | saucier import --check` must not exit 0."""
    cli.main(["parse"])
    capsys.readouterr()
    cli.main(["export"])
    head = "".join(capsys.readouterr().out.splitlines(keepends=True)[:2])
    monkeypatch.setattr(sys, "stdin", io.StringIO(head))
    assert cli.main(["import", "--check"]) == cli.FAILED
    out, err = capsys.readouterr()
    assert out == ""
    assert err == (
        "saucier: line 1: catalogue 'escoffier-1909' states 151 preparations, "
        "the stream carries 0\n"
    )


@pytest.mark.unit
def test_import_without_check_is_refused(capsys):
    with pytest.raises(SystemExit) as stopped:
        cli.main(["import"])
    assert stopped.value.code == 2
    assert "--check" in capsys.readouterr().err


@pytest.mark.unit
def test_import_reports_a_rejected_line_on_stderr(capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"schema":"saucier/9"}\n'))
    assert cli.main(["import", "--check"]) == cli.FAILED
    out, err = capsys.readouterr()
    assert out == ""
    assert err.startswith("saucier: line 1: unknown schema 'saucier/9'")


@pytest.mark.unit
def test_import_of_an_empty_stream_fails_and_prints_no_success(capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert cli.main(["import", "--check"]) == cli.FAILED
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "saucier: interchange carries no catalogues\n"


@pytest.mark.corpus
def test_a_failed_export_cannot_be_validated_as_a_success(wired, capsys, monkeypatch):
    """The pipe shape: export fails before its first record, import sees nothing."""
    assert cli.main(["export"]) == cli.FAILED
    exported, err = capsys.readouterr()
    assert exported == ""
    assert "no catalogue stored" in err
    monkeypatch.setattr(sys, "stdin", io.StringIO(exported))
    assert cli.main(["import", "--check"]) == cli.FAILED
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "saucier: interchange carries no catalogues\n"


@pytest.mark.corpus
def test_two_exports_concatenated_are_rejected_at_the_first_repeated_id(
    wired, capsys, monkeypatch
):
    cli.main(["parse"])
    capsys.readouterr()
    cli.main(["export"])
    exported = capsys.readouterr().out
    monkeypatch.setattr(sys, "stdin", io.StringIO(exported + exported))
    assert cli.main(["import", "--check"]) == cli.FAILED
    out, err = capsys.readouterr()
    assert out == ""
    assert err == (
        "saucier: line 294: duplicate id 'escoffier-1909', first seen at line 1\n"
    )


@pytest.mark.corpus
def test_export_exits_clean_when_the_reader_closes_the_pipe(
    wired, capsys, monkeypatch, tmp_path
):
    """`saucier export | head -n 1` must not end in a traceback."""
    cli.main(["parse"])
    capsys.readouterr()

    class Closed:
        def __init__(self, handle):
            self.handle = handle

        def writelines(self, _):
            raise BrokenPipeError

        def fileno(self):
            return self.handle.fileno()

    with (tmp_path / "sink").open("w") as handle:
        monkeypatch.setattr(sys, "stdout", Closed(handle))
        assert cli.main(["export"]) == 0


@pytest.mark.corpus
def test_a_closed_pipe_on_a_stdout_with_no_descriptor_still_exits_clean(
    wired, capsys, monkeypatch
):
    """A harness stdout has no fileno. The handler must not chain a traceback."""
    cli.main(["parse"])
    capsys.readouterr()

    class Closed:
        def writelines(self, _):
            raise BrokenPipeError

    monkeypatch.setattr(sys, "stdout", Closed())
    assert cli.main(["export"]) == 0


@pytest.mark.corpus
def test_every_command_exits_clean_when_the_reader_closes_the_pipe(
    wired, capsys, monkeypatch
):
    """`saucier diff ... | head -1` used to exit 120 with an ignored exception."""
    cli.main(["parse"])
    capsys.readouterr()

    class Closed:
        def write(self, _):
            raise BrokenPipeError

        def flush(self):
            raise BrokenPipeError

    monkeypatch.setattr(sys, "stdout", Closed())
    assert cli.main(["diff", FIRST_PRINTING.source_id, REVISION.source_id]) == 0


@pytest.mark.unit
def test_import_with_standard_input_closed_is_refused(capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", None)
    assert cli.main(["import", "--check"]) == cli.FAILED
    assert capsys.readouterr().err == "saucier: standard input is closed\n"
