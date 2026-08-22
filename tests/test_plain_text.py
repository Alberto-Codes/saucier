import pytest

from saucier.adapters.driven.plain_text import PlainText
from saucier.domain.errors import SourceUnreadable
from saucier.domain.witness import Fidelity

SCAN = [
    "A   GUIDE  TO",
    "MODERN    COOKERY",
    "Copyright  1907  hy  William  Heinemann",
    "22—BROWN  SAUCE",
]


def source(path):
    return PlainText(
        path=path,
        work="book",
        origin="a test fixture",
        fidelity=Fidelity.OCR,
    )


@pytest.fixture
def scanned(tmp_path):
    path = tmp_path / "scan.txt"
    path.write_text("\n".join(SCAN) + "\n", encoding="utf-8")
    return path


@pytest.mark.unit
def test_the_whole_file_is_the_body(scanned):
    assert source(scanned).lines() == SCAN


@pytest.mark.unit
def test_nothing_is_stripped_so_the_offset_is_zero(scanned):
    reader = source(scanned)
    assert reader.line_offset == 0
    assert reader.lines()[0] == SCAN[0]


@pytest.mark.unit
def test_the_reader_names_the_source_from_what_the_scan_states(scanned):
    assert source(scanned).witness.source_id == "book-1907"
    assert source(scanned).witness.fidelity == Fidelity.OCR


@pytest.mark.unit
def test_a_missing_file_is_reported(tmp_path):
    with pytest.raises(SourceUnreadable, match="cannot read source"):
        source(tmp_path / "absent.txt").lines()


@pytest.mark.unit
def test_a_file_that_is_not_utf_8_is_reported(tmp_path):
    path = tmp_path / "latin.txt"
    path.write_bytes("sauce b\xe9arnaise".encode("latin-1"))
    with pytest.raises(SourceUnreadable, match="not UTF-8"):
        source(path).lines()


@pytest.mark.unit
def test_the_body_is_a_copy_a_caller_cannot_corrupt(scanned):
    reader = source(scanned)
    reader.lines().append("forged entry")
    assert reader.lines() == SCAN
