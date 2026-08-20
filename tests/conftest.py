import pytest

from saucier.infrastructure.bootstrap import escoffier_source
from saucier.services.extraction import extract


@pytest.fixture(scope="session")
def escoffier():
    """The real catalogue, parsed once for every corpus test."""
    return extract(escoffier_source())
