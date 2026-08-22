from types import SimpleNamespace

import pytest

from saucier.domain.witness import Edition, Fidelity, Witness
from saucier.infrastructure.bootstrap import escoffier_sources
from saucier.services.extraction import extract

REVISION = SimpleNamespace(
    source_id="escoffier-1909", sauces=124, derived=50, unresolved=74
)
"""The numbers the README, the tutorial, and the docs home page publish.

Changing them is a deliberate act: update those pages in the same commit,
and say why in the changelog. Two published posts quote them as well.
"""

FIRST_PRINTING = SimpleNamespace(
    source_id="escoffier-1907", sauces=113, derived=35, unresolved=78
)
"""The 1907 witness, which is OCR. Published from release 0.3.0 onward."""


def a_witness(source_id="test-1900", fidelity=Fidelity.TRANSCRIPTION):
    """Build a witness for a fixture, named for the id a test wants."""
    work, _, year = source_id.rpartition("-")
    return Witness(
        work=work,
        origin="a test fixture",
        fidelity=fidelity,
        edition=Edition(
            statement=None,
            stated_year=None,
            impression=None,
            copyright_year=int(year),
        ),
    )


@pytest.fixture(scope="session")
def escoffier():
    """The 1909 revision, parsed once for every corpus test."""
    return extract(escoffier_sources()[0])


@pytest.fixture(scope="session")
def escoffier_1907():
    """The 1907 first printing, parsed once for every corpus test."""
    return extract(escoffier_sources()[1])


@pytest.fixture
def census():
    """The published census, so tests and documentation cannot drift apart."""
    return REVISION


@pytest.fixture
def first_printing_census():
    """The census of the scanned witness."""
    return FIRST_PRINTING
