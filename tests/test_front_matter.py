import pytest

from saucier.domain.errors import EditionUnstated
from saucier.services.front_matter import FRONT_MATTER, read_edition

HISTORY = [
    "                            _WITH PORTRAIT_",
    "",
    "                        NEW AND REVISED EDITION",
    "",
    "                       LONDON: WILLIAM HEINEMANN",
    "",
    "        _First Printed, May 1907",
    "     Second Impression, December 1907",
    "  New and Revised Edition, January 1909",
    " New Impressions, August 1911, May 1913,",
    "        March 1916, January 1920._",
    "",
    "_Copyright 1907 by William Heinemann._",
]

SCANNED_TITLE_PAGE = [
    "A GUIDE TO",
    "MODERN COOKERY",
    "BY",
    "A. ESCOFFIER",
    "OF THE CAHI-TON HOTEL",
    "LONDON",
    "WILLIAM HEINEMANN",
    "190;",
    "Copyright 1907 hy William Heinemann",
]


@pytest.mark.unit
def test_the_edition_is_the_last_printing_the_history_calls_an_edition():
    edition = read_edition(HISTORY)
    assert edition.statement == "New and Revised Edition, January 1909"
    assert edition.stated_year == 1909


@pytest.mark.unit
def test_the_impression_is_the_last_printing_of_all():
    """The copy in hand, and it continues onto a second line."""
    assert read_edition(HISTORY).impression == "January 1920"


@pytest.mark.unit
def test_the_copyright_year_is_read_apart_from_the_edition():
    edition = read_edition(HISTORY)
    assert edition.copyright_year == 1907
    assert edition.year == 1909


@pytest.mark.unit
def test_a_title_page_with_no_printing_history_states_no_edition():
    """A revision announces itself. A first printing has nothing to print."""
    edition = read_edition(SCANNED_TITLE_PAGE)
    assert edition.statement is None
    assert edition.impression is None
    assert edition.year == 1907


@pytest.mark.unit
def test_a_scanned_copyright_line_survives_its_own_mangling():
    """`by` reads as `hy`, and the year is what the pattern needs."""
    assert read_edition(SCANNED_TITLE_PAGE).copyright_year == 1907


@pytest.mark.unit
def test_a_text_stating_no_identity_is_reported_rather_than_named():
    with pytest.raises(EditionUnstated, match="no edition and no copyright year"):
        read_edition(["A GUIDE TO", "MODERN COOKERY", "BY", "A. ESCOFFIER"])


@pytest.mark.unit
def test_a_date_deeper_than_the_front_matter_is_prose_not_a_printing():
    lines = ["Copyright 1907 by William Heinemann"]
    lines += ["filler"] * FRONT_MATTER
    lines += ["Second Impression, December 1999"]
    assert read_edition(lines).impression is None
