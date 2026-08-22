import pytest

from saucier.adapters.driven.gutenberg import END, START, GutenbergText
from saucier.domain.errors import SourceUnreadable
from saucier.domain.witness import Fidelity

HEADER = ["The Project Gutenberg eBook of Something", "", "Licence blurb."]
BODY = ["22—BROWN SAUCE", "Reduce the wine.", "Copyright 1907 by A Publisher"]
FOOTER = ["Section: Full Project Gutenberg License", "Donations accepted."]


def source(path):
    return GutenbergText(
        path=path,
        work="book",
        origin="a test fixture",
        fidelity=Fidelity.TRANSCRIPTION,
    )


def write(tmp_path, lines, name="book.txt"):
    path = tmp_path / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def wrapped(tmp_path):
    return write(tmp_path, [*HEADER, START, *BODY, END, *FOOTER])


@pytest.mark.unit
def test_the_licence_wrapper_never_reaches_an_extractor(wrapped):
    assert source(wrapped).lines() == BODY


@pytest.mark.unit
def test_the_offset_names_the_line_the_body_starts_on(wrapped):
    reader = source(wrapped)
    # Three header lines and the start marker come first.
    assert reader.line_offset == 4
    body_index = 0
    file_line = reader.line_offset + body_index + 1
    assert wrapped.read_text(encoding="utf-8").splitlines()[file_line - 1] == BODY[0]


@pytest.mark.unit
def test_a_missing_file_is_reported(tmp_path):
    with pytest.raises(SourceUnreadable, match="cannot read source"):
        source(tmp_path / "absent.txt").lines()


@pytest.mark.unit
def test_a_file_without_the_start_marker_is_reported(tmp_path):
    path = write(tmp_path, [*HEADER, *BODY])
    with pytest.raises(SourceUnreadable, match="no Gutenberg start marker"):
        source(path).lines()


@pytest.mark.unit
def test_a_truncated_file_is_reported_rather_than_silently_kept(tmp_path):
    path = write(tmp_path, [*HEADER, START, *BODY])
    with pytest.raises(SourceUnreadable, match="no Gutenberg end marker"):
        source(path).lines()


@pytest.mark.unit
def test_a_file_that_is_not_utf_8_is_reported(tmp_path):
    path = tmp_path / "latin.txt"
    body = f"{START}\nsauce b\xe9arnaise\n{END}"
    path.write_bytes(body.encode("latin-1"))
    with pytest.raises(SourceUnreadable, match="not UTF-8"):
        source(path).lines()


@pytest.mark.unit
def test_the_body_is_a_copy_a_caller_cannot_corrupt(wrapped):
    reader = source(wrapped)
    reader.lines().append("forged entry")
    assert reader.lines() == BODY


@pytest.mark.unit
def test_the_reader_names_the_source_from_what_the_text_states(wrapped):
    """Not from the path, which is `book.txt` and says 1907 nowhere."""
    assert source(wrapped).witness.source_id == "book-1907"


@pytest.mark.unit
def test_a_file_with_no_markers_is_still_refused(tmp_path):
    """The Archive scan has none, and this adapter must not stretch to fit."""
    path = write(tmp_path, ["A GUIDE TO", "MODERN COOKERY", "Copyright 1907 by X"])
    with pytest.raises(SourceUnreadable, match="no Gutenberg start marker"):
        assert source(path).witness
