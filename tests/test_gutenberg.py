import pytest

from saucier.adapters.driven.gutenberg import END, START, GutenbergText
from saucier.domain.errors import SourceUnreadable

HEADER = ["The Project Gutenberg eBook of Something", "", "Licence blurb."]
BODY = ["22—BROWN SAUCE", "Reduce the wine."]
FOOTER = ["Section: Full Project Gutenberg License", "Donations accepted."]


def write(tmp_path, lines, name="book.txt"):
    path = tmp_path / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def wrapped(tmp_path):
    return write(tmp_path, [*HEADER, START, *BODY, END, *FOOTER])


@pytest.mark.unit
def test_the_licence_wrapper_never_reaches_an_extractor(wrapped):
    assert GutenbergText(wrapped, "book").lines() == BODY


@pytest.mark.unit
def test_the_offset_names_the_line_the_body_starts_on(wrapped):
    source = GutenbergText(wrapped, "book")
    # Three header lines and the start marker come first.
    assert source.line_offset == 4
    body_index = 0
    file_line = source.line_offset + body_index + 1
    assert wrapped.read_text(encoding="utf-8").splitlines()[file_line - 1] == BODY[0]


@pytest.mark.unit
def test_a_missing_file_is_reported(tmp_path):
    with pytest.raises(SourceUnreadable, match="cannot read source"):
        GutenbergText(tmp_path / "absent.txt", "book").lines()


@pytest.mark.unit
def test_a_file_without_the_start_marker_is_reported(tmp_path):
    path = write(tmp_path, [*HEADER, *BODY])
    with pytest.raises(SourceUnreadable, match="no Gutenberg start marker"):
        GutenbergText(path, "book").lines()


@pytest.mark.unit
def test_a_truncated_file_is_reported_rather_than_silently_kept(tmp_path):
    path = write(tmp_path, [*HEADER, START, *BODY])
    with pytest.raises(SourceUnreadable, match="no Gutenberg end marker"):
        GutenbergText(path, "book").lines()


@pytest.mark.unit
def test_a_file_that_is_not_utf_8_is_reported(tmp_path):
    path = tmp_path / "latin.txt"
    body = f"{START}\nsauce b\xe9arnaise\n{END}"
    path.write_bytes(body.encode("latin-1"))
    with pytest.raises(SourceUnreadable, match="not UTF-8"):
        GutenbergText(path, "book").lines()


@pytest.mark.unit
def test_the_body_is_a_copy_a_caller_cannot_corrupt(wrapped):
    source = GutenbergText(wrapped, "book")
    source.lines().append("forged entry")
    assert source.lines() == BODY
