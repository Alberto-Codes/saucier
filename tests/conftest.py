from types import SimpleNamespace

import pytest

from saucier.infrastructure.bootstrap import escoffier_source
from saucier.services.extraction import extract

CENSUS = SimpleNamespace(sauces=124, derived=50, unresolved=74)
"""The numbers the README, the tutorial, and the docs home page publish.

Changing them is a deliberate act: update those pages in the same commit,
and say why in the changelog.
"""


@pytest.fixture(scope="session")
def escoffier():
    """The real catalogue, parsed once for every corpus test."""
    return extract(escoffier_source())


@pytest.fixture
def census():
    """The published census, so tests and documentation cannot drift apart."""
    return CENSUS
