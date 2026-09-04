import io
import json
from dataclasses import replace
from pathlib import Path

import pytest
from conftest import a_witness

from saucier.adapters.driven.jsonl import SCHEMA, JsonlInterchange, preparation_id
from saucier.domain.errors import CatalogueUnwritable, RecordRejected
from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
from saucier.domain.types import ConceptId, Language
from saucier.domain.witness import Edition, Fidelity, Witness

REVISION = Witness(
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
SCAN = a_witness("fixture-1907", Fidelity.OCR)


def a_preparation(witness, title, entry, line, parent, language=Language.ENGLISH):
    return Preparation(
        title=title,
        terms=(Term(title, language),),
        body=f"Prose of {title}.",
        ref=SourceRef(
            source_id=witness.source_id,
            entry=entry,
            line=line,
            fidelity=witness.fidelity,
        ),
        parent=parent,
    )


@pytest.fixture
def revision():
    return Catalogue(
        witness=REVISION,
        preparations=(
            a_preparation(
                REVISION,
                "ORDINARY VELOUTÉ SAUCE",
                25,
                900,
                ConceptId("pale-roux"),
                Language.FRENCH,
            ),
            a_preparation(REVISION, "MARROW SAUCE", 26, 950, None),
        ),
        mothers=frozenset({ConceptId("veloute"), ConceptId("espagnole")}),
        entries_read=2963,
    )


@pytest.fixture
def scan():
    """Two preparations at one entry number, as the 1907 scan has at 138."""
    return Catalogue(
        witness=SCAN,
        preparations=(
            a_preparation(SCAN, "HORSE-RADISH SAUCE", 138, 4100, None),
            a_preparation(
                SCAN, "WHISKED MAYONNAISE", 138, 4120, ConceptId("horse-radish")
            ),
        ),
        mothers=frozenset({ConceptId("espagnole")}),
        entries_read=None,
    )


def lines_of(*catalogues):
    return list(JsonlInterchange().encode(catalogues))


def decode(lines):
    return JsonlInterchange().decode(lines)


def edit(line, **changes):
    """Rewrite one record with some fields changed, keeping it one line."""
    record = json.loads(line)
    for key, value in changes.items():
        if value is ...:
            del record[key]
        else:
            record[key] = value
    return json.dumps(record, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------- #
# The round trip
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_a_catalogue_survives_a_round_trip_through_a_text_stream(revision):
    stream = io.StringIO()
    stream.writelines(JsonlInterchange().encode([revision]))
    stream.seek(0)
    assert decode(stream) == (revision,)


@pytest.mark.unit
def test_two_catalogues_coexist_in_one_stream(revision, scan):
    assert decode(lines_of(revision, scan)) == (revision, scan)


@pytest.mark.unit
def test_encoding_the_same_input_twice_yields_identical_text(revision, scan):
    assert lines_of(revision, scan) == lines_of(revision, scan)


@pytest.mark.unit
def test_catalogue_records_come_first_then_preparations_in_source_order(revision, scan):
    kinds = [json.loads(line)["type"] for line in lines_of(revision, scan)]
    assert kinds == ["catalogue", "catalogue"] + ["preparation"] * 4
    ids = [json.loads(line)["id"] for line in lines_of(revision, scan)]
    assert ids[2:] == [
        "fixture-1909:line:900",
        "fixture-1909:line:950",
        "fixture-1907:line:4100",
        "fixture-1907:line:4120",
    ]


@pytest.mark.unit
def test_every_line_is_one_json_object_ending_in_one_newline(revision, scan):
    for line in lines_of(revision, scan):
        assert line.endswith("\n") and not line.endswith("\n\n")
        record = json.loads(line)
        assert record["schema"] == SCHEMA
        assert set(record) >= {"schema", "type", "id"}


@pytest.mark.unit
def test_accented_surfaces_and_language_tags_survive_exactly(revision):
    lines = lines_of(revision)
    assert "VELOUTÉ" in lines[1]
    assert "\\u00c9" not in lines[1]
    rebuilt = decode(lines)[0].preparations[0]
    assert rebuilt.title == "ORDINARY VELOUTÉ SAUCE"
    assert rebuilt.terms[0].language is Language.FRENCH


@pytest.mark.unit
def test_an_unresolved_parent_is_null_and_stays_unresolved(revision):
    lines = lines_of(revision)
    assert json.loads(lines[2])["parent"] is None
    assert decode(lines)[0].preparations[1].parent is None


@pytest.mark.unit
def test_a_catalogue_record_carries_what_rebuilds_the_frame(revision, scan):
    first, second = (json.loads(line) for line in lines_of(revision, scan)[:2])
    assert first["id"] == "fixture-1909"
    assert first["edition"]["statement"] == "New and Revised Edition, January 1909"
    assert first["fidelity"] == "transcription"
    assert first["mothers"] == ["espagnole", "veloute"]
    assert first["entries_read"] == 2963
    assert second["entries_read"] is None
    assert second["edition"]["stated_year"] is None


@pytest.mark.unit
def test_a_preparation_record_names_its_catalogue_and_its_line(revision):
    record = json.loads(lines_of(revision)[1])
    assert record["catalogue"] == "fixture-1909"
    assert record["id"] == preparation_id("fixture-1909", 900)
    assert record["ref"] == {"entry": 25, "line": 900, "fidelity": "transcription"}
    assert record["terms"] == [
        {
            "surface": "ORDINARY VELOUTÉ SAUCE",
            "language": "fr",
            "concept": "ordinary-veloute-sauce",
        }
    ]


@pytest.mark.unit
def test_a_repeated_entry_number_does_not_collide(scan):
    ids = {json.loads(line)["id"] for line in lines_of(scan)[1:]}
    assert ids == {"fixture-1907:line:4100", "fixture-1907:line:4120"}
    rebuilt = decode(lines_of(scan))[0]
    assert [p.ref.entry for p in rebuilt.preparations] == [138, 138]
    assert rebuilt.preparations[1].parent == "horse-radish"


@pytest.mark.unit
def test_records_may_arrive_in_any_order(revision, scan):
    """Preparations before their catalogue, catalogues reversed."""
    lines = lines_of(revision, scan)
    shuffled = [lines[4], lines[2], lines[1], lines[5], lines[0], lines[3]]
    assert decode(shuffled) == (scan, revision)


@pytest.mark.unit
def test_preparations_keep_the_order_their_records_arrived_in(revision):
    """A catalogue whose lines do not ascend is legal, and must read back equal."""
    descending = replace(revision, preparations=revision.preparations[::-1])
    assert decode(lines_of(descending)) == (descending,)
    lines = lines_of(revision)
    swapped = decode([lines[0], lines[2], lines[1]])[0]
    assert swapped == descending


@pytest.mark.unit
def test_two_preparations_on_one_line_are_refused_before_any_output(revision):
    first, second = revision.preparations
    clash = replace(second, ref=replace(second.ref, line=first.ref.line))
    doubled = replace(revision, preparations=(first, clash))
    with pytest.raises(
        CatalogueUnwritable,
        match="holds ORDINARY VELOUTÉ SAUCE and MARROW SAUCE at line 900",
    ):
        list(JsonlInterchange().encode([doubled]))


@pytest.mark.unit
def test_blank_lines_are_skipped_and_still_counted(revision):
    lines = lines_of(revision)
    padded = ["\n", lines[0], "   \n", lines[1], lines[2], "\n"]
    assert decode(padded) == (revision,)
    with pytest.raises(RecordRejected, match=r"^line 4: "):
        decode([*padded[:3], "{", *padded[4:]])


@pytest.mark.unit
def test_an_empty_stream_rebuilds_nothing():
    assert decode(io.StringIO("")) == ()


@pytest.mark.unit
def test_a_catalogue_with_no_preparations_rebuilds_empty(revision):
    bare = replace(revision, preparations=())
    assert decode(lines_of(bare)) == (bare,)


# --------------------------------------------------------------------------- #
# What the reader rejects
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_malformed_json_is_rejected_with_its_line_number(revision):
    lines = lines_of(revision)
    with pytest.raises(
        RecordRejected, match=r"^line 2: not JSON \(Expecting value at column 30\)"
    ):
        decode([lines[0], '{"schema":"saucier/1","type":', lines[2]])
    # The newline is skipped as whitespace before the parser gives up.
    with pytest.raises(
        RecordRejected, match=r"^line 1: not JSON \(Expecting value at column 31\)"
    ):
        decode(['{"schema":"saucier/1","type":\n'])


@pytest.mark.unit
def test_a_line_nested_too_deep_is_rejected_with_its_line_number():
    with pytest.raises(RecordRejected, match=r"^line 1: not JSON \(nested too deep\)"):
        decode(["[" * 100_000 + "\n"])


@pytest.mark.unit
def test_a_repeated_key_is_rejected_rather_than_read_last_wins(revision):
    """`json` keeps the last value of a repeated key. A rewritten parent must not pass."""
    lines = lines_of(revision)
    resolved = lines[1].rstrip("\n")
    with pytest.raises(
        RecordRejected, match=r"line 2: object repeats a key: \['parent'\]"
    ):
        decode([lines[0], resolved[:-1] + ',"parent":null}\n', lines[2]])


@pytest.mark.unit
def test_a_stream_cut_at_a_line_boundary_is_rejected(revision, scan):
    lines = lines_of(revision, scan)
    with pytest.raises(
        RecordRejected,
        match=r"line 2: catalogue 'fixture-1907' states 2 preparations, the stream carries 0",
    ):
        decode(lines[:4])
    with pytest.raises(
        RecordRejected,
        match=r"line 1: catalogue 'fixture-1909' states 2 preparations, the stream carries 1",
    ):
        decode(lines[:3] + lines[4:])


@pytest.mark.unit
def test_a_catalogue_record_that_understates_its_preparations_is_rejected(revision):
    lines = lines_of(revision)
    with pytest.raises(
        RecordRejected, match=r"states 1 preparations, the stream carries 2"
    ):
        decode([edit(lines[0], preparations=1), *lines[1:]])
    with pytest.raises(RecordRejected, match=r"line 1: a catalogue cannot state -1"):
        decode([edit(lines[0], preparations=-1), *lines[1:]])


@pytest.mark.unit
def test_a_byte_that_is_not_utf8_is_rejected_with_its_line(revision):
    lines = lines_of(revision)
    raw = (
        lines[0].encode()
        + lines[1].encode().replace(b"Prose", b"Pr\xffose")
        + lines[2].encode()
    )
    offset = lines[1].encode().index(b"Prose") + 2
    with pytest.raises(
        RecordRejected,
        match=rf"^line 2: not UTF-8 \(invalid start byte at byte {offset} of the line\)",
    ):
        decode(line.decode("utf-8") for line in io.BytesIO(raw))


@pytest.mark.unit
def test_a_language_or_fidelity_tag_the_domain_does_not_know_is_rejected(revision):
    lines = lines_of(revision)
    terms = [{"surface": "MARROW SAUCE", "language": "xx", "concept": "marrow-sauce"}]
    with pytest.raises(RecordRejected, match=r"line 3: 'xx' is not a valid Language"):
        decode([lines[0], lines[1], edit(lines[2], terms=terms)])
    with pytest.raises(RecordRejected, match=r"line 1: 'scan' is not a valid Fidelity"):
        decode([edit(lines[0], fidelity="scan"), *lines[1:]])


@pytest.mark.unit
def test_the_bytes_of_one_record_are_pinned(revision):
    """Key order, separators, null, and the newline, in one literal."""
    assert lines_of(revision)[2] == (
        '{"schema":"saucier/1","type":"preparation","id":"fixture-1909:line:950",'
        '"catalogue":"fixture-1909","title":"MARROW SAUCE",'
        '"terms":[{"surface":"MARROW SAUCE","language":"en","concept":"marrow-sauce"}],'
        '"concept":"marrow-sauce","parent":null,'
        '"ref":{"entry":26,"line":950,"fidelity":"transcription"},'
        '"body":"Prose of MARROW SAUCE."}\n'
    )


@pytest.mark.unit
def test_a_line_that_is_json_but_not_an_object_is_rejected():
    with pytest.raises(
        RecordRejected, match="line 1: a record is a JSON object, not list"
    ):
        decode(["[1, 2]\n"])


@pytest.mark.unit
def test_an_unknown_schema_is_rejected(revision):
    lines = lines_of(revision)
    with pytest.raises(RecordRejected, match="line 1: unknown schema 'saucier/2'"):
        decode([edit(lines[0], schema="saucier/2"), *lines[1:]])
    with pytest.raises(RecordRejected, match="line 1: unknown schema None"):
        decode([edit(lines[0], schema=...), *lines[1:]])


@pytest.mark.unit
def test_an_unknown_record_type_is_rejected(revision):
    lines = lines_of(revision)
    with pytest.raises(RecordRejected, match="line 2: unknown record type 'claim'"):
        decode([lines[0], edit(lines[1], type="claim"), lines[2]])


@pytest.mark.unit
def test_a_record_without_an_id_is_rejected(revision):
    lines = lines_of(revision)
    with pytest.raises(RecordRejected, match="line 1: a record needs an id"):
        decode([edit(lines[0], id=""), *lines[1:]])
    with pytest.raises(RecordRejected, match="line 1: a record needs an id"):
        decode([edit(lines[0], id=...), *lines[1:]])


@pytest.mark.unit
def test_a_duplicate_catalogue_id_is_rejected(revision):
    """One catalogue per source id. A second text of one edition needs lab #60."""
    lines = lines_of(revision)
    with pytest.raises(
        RecordRejected,
        match=r"line 4: duplicate id 'fixture-1909', first seen at line 1",
    ):
        decode([*lines, lines[0]])


@pytest.mark.unit
def test_two_complete_streams_concatenated_are_rejected_at_the_first_repeat(
    revision, scan
):
    """`saucier export` writes every catalogue, so two exports cannot be joined."""
    lines = lines_of(revision, scan)
    with pytest.raises(
        RecordRejected,
        match=r"line 7: duplicate id 'fixture-1909', first seen at line 1",
    ):
        decode(lines + lines)


@pytest.mark.unit
def test_a_duplicate_preparation_id_is_rejected_naming_both_lines(revision):
    lines = lines_of(revision)
    with pytest.raises(
        RecordRejected, match=r"line 4: duplicate id .*line:900.*first seen at line 2"
    ):
        decode([*lines, lines[1]])


@pytest.mark.unit
def test_a_preparation_whose_catalogue_is_absent_is_rejected(revision):
    lines = lines_of(revision)
    with pytest.raises(
        RecordRejected,
        match="line 1: preparation names catalogue 'fixture-1909', which",
    ):
        decode(lines[1:])


@pytest.mark.unit
def test_a_field_the_schema_does_not_name_is_rejected(revision):
    lines = lines_of(revision)
    with pytest.raises(
        RecordRejected,
        match=r"line 2: preparation record fields: absent \[\], unexpected \['chapter'\]",
    ):
        decode([lines[0], edit(lines[1], chapter="warm"), lines[2]])
    with pytest.raises(
        RecordRejected, match=r"line 1: catalogue record fields: absent \['origin'\]"
    ):
        decode([edit(lines[0], origin=...), *lines[1:]])


@pytest.mark.unit
def test_a_blank_parent_is_damage_not_an_absence_of_evidence(revision):
    lines = lines_of(revision)
    with pytest.raises(
        RecordRejected, match="line 3: surface form yields an empty concept id"
    ):
        decode([lines[0], lines[1], edit(lines[2], parent="")])


@pytest.mark.unit
def test_a_parent_that_is_not_its_own_fold_is_rejected(revision):
    lines = lines_of(revision)
    with pytest.raises(RecordRejected, match="line 2: 'Pale Roux' is not a concept id"):
        decode([lines[0], edit(lines[1], parent="Pale Roux"), lines[2]])


@pytest.mark.unit
def test_a_concept_that_disagrees_with_its_terms_is_rejected(revision):
    lines = lines_of(revision)
    with pytest.raises(
        RecordRejected, match="line 2: concept 'veloute' is not folded from the terms"
    ):
        decode([lines[0], edit(lines[1], concept="veloute"), lines[2]])


@pytest.mark.unit
def test_an_id_that_does_not_address_its_line_is_rejected(revision):
    lines = lines_of(revision)
    with pytest.raises(
        RecordRejected, match="line 2: id 'fixture-1909:entry:25' does not address"
    ):
        decode([lines[0], edit(lines[1], id="fixture-1909:entry:25"), lines[2]])


@pytest.mark.unit
def test_a_catalogue_record_that_misnames_itself_is_rejected(revision):
    lines = lines_of(revision)
    with pytest.raises(
        RecordRejected,
        match="line 1: catalogue record 'fixture-1800' describes 'fixture-1909'",
    ):
        decode([edit(lines[0], id="fixture-1800"), *lines[1:]])


@pytest.mark.unit
def test_a_wrong_type_in_a_field_is_rejected(revision):
    lines = lines_of(revision)
    with pytest.raises(
        RecordRejected, match="line 1: expected a whole number, not '2963'"
    ):
        decode([edit(lines[0], entries_read="2963"), *lines[1:]])
    with pytest.raises(
        RecordRejected, match="line 1: expected a whole number, not True"
    ):
        decode([edit(lines[0], entries_read=True), *lines[1:]])
    with pytest.raises(RecordRejected, match="line 2: expected a string, not 7"):
        decode([lines[0], edit(lines[1], title=7), lines[2]])
    with pytest.raises(RecordRejected, match="line 2: terms is not a JSON array"):
        decode([lines[0], edit(lines[1], terms="none"), lines[2]])
    with pytest.raises(RecordRejected, match="line 2: ref is not a JSON object"):
        decode([lines[0], edit(lines[1], ref=[]), lines[2]])


@pytest.mark.unit
def test_an_unstated_edition_is_rejected(revision):
    lines = lines_of(revision)
    edition = {
        "statement": None,
        "stated_year": None,
        "impression": None,
        "copyright_year": None,
    }
    with pytest.raises(RecordRejected, match="line 1: front matter states neither"):
        decode([edit(lines[0], edition=edition), *lines[1:]])


@pytest.mark.unit
def test_repeated_mothers_are_rejected_rather_than_collapsed(revision):
    lines = lines_of(revision)
    with pytest.raises(RecordRejected, match="line 1: mothers repeat a concept"):
        decode([edit(lines[0], mothers=["veloute", "veloute"]), *lines[1:]])


@pytest.mark.unit
def test_a_term_whose_concept_disagrees_is_rejected(revision):
    lines = lines_of(revision)
    terms = [{"surface": "MARROW SAUCE", "language": "en", "concept": "marrow"}]
    with pytest.raises(
        RecordRejected,
        match="line 3: concept 'marrow' is not folded from 'MARROW SAUCE'",
    ):
        decode([lines[0], lines[1], edit(lines[2], terms=terms)])


@pytest.mark.unit
def test_a_missing_nested_field_is_reported_by_name(revision):
    lines = lines_of(revision)
    with pytest.raises(RecordRejected, match=r"line 2: ref fields: absent \['line'\]"):
        decode(
            [
                lines[0],
                edit(lines[1], ref={"entry": 25, "fidelity": "transcription"}),
                lines[2],
            ]
        )


@pytest.mark.unit
def test_a_catalogue_the_domain_refuses_is_rejected(revision):
    """A preparation citing another fidelity than its catalogue's witness."""
    lines = lines_of(revision)
    ref = {"entry": 25, "line": 900, "fidelity": "ocr"}
    with pytest.raises(
        RecordRejected,
        match="line 2: ORDINARY VELOUTÉ SAUCE cites fixture-1909 at ocr, "
        "in a catalogue at transcription",
    ):
        decode([lines[0], edit(lines[1], ref=ref), lines[2]])


# --------------------------------------------------------------------------- #
# The committed corpus
# --------------------------------------------------------------------------- #


@pytest.mark.corpus
def test_both_corpus_catalogues_survive_the_round_trip(escoffier, escoffier_1907):
    lines = lines_of(escoffier, escoffier_1907)
    assert decode(lines) == (escoffier, escoffier_1907)


@pytest.mark.corpus
def test_the_published_census_is_unchanged_by_the_round_trip(
    escoffier, escoffier_1907, census, first_printing_census
):
    revision, first = decode(lines_of(escoffier, escoffier_1907))
    for rebuilt, published in ((revision, census), (first, first_printing_census)):
        assert rebuilt.source_id == published.source_id
        assert len(rebuilt.preparations) == published.sauces
        assert rebuilt.resolved == published.derived
        assert rebuilt.unresolved == published.unresolved


@pytest.mark.corpus
def test_the_corpus_stream_is_deterministic_and_its_ids_are_unique(
    escoffier, escoffier_1907
):
    text = "".join(lines_of(escoffier, escoffier_1907))
    assert text == "".join(lines_of(escoffier, escoffier_1907))
    ids = [json.loads(line)["id"] for line in text.splitlines()]
    assert len(ids) == len(set(ids)) == 2 + 151 + 140


@pytest.mark.corpus
def test_the_scan_catalogue_carries_two_preparations_at_entry_138_under_two_ids(
    escoffier_1907,
):
    records = [json.loads(line) for line in lines_of(escoffier_1907)[1:]]
    at_138 = [r["id"] for r in records if r["ref"]["entry"] == 138]
    assert len(at_138) == 2
    assert len(set(at_138)) == 2


DOCUMENTED = (
    "README.md",
    "docs/adr/0016-jsonl-is-the-interchange-not-a-store.md",
    "docs/reference/cli.md",
    "docs/reference/data-model.md",
    "docs/tutorial/first-run.md",
)
"""Every page that quotes a record. A quoted line is real output or a prefix of it."""


@pytest.mark.corpus
def test_every_documented_record_is_real_output(escoffier, escoffier_1907):
    real = [line.rstrip("\n") for line in lines_of(escoffier, escoffier_1907)]
    root = Path(__file__).resolve().parent.parent
    quoted = 0
    for page in DOCUMENTED:
        for text in (root / page).read_text(encoding="utf-8").splitlines():
            if text.startswith('{"schema":"saucier/1"'):
                quoted += 1
                assert any(line == text or line.startswith(text) for line in real), (
                    f"{page} quotes a record that is not real output: {text[:80]}"
                )
    assert quoted >= 8
