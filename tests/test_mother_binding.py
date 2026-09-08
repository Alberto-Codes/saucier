"""A derivative that states its mother cannot establish that mother's identity
through a name run."""

from dataclasses import replace

import pytest
from conftest import a_witness

from saucier.domain.models import Catalogue, Preparation, SourceRef, Term
from saucier.domain.types import ConceptId, Language
from saucier.domain.witness import Fidelity


@pytest.mark.unit
@pytest.mark.parametrize(
    ("body", "binds"),
    [
        ("Use Espagnole with fish stock.", False),
        ("Use ESPAGNOLE with fish stock.", False),
        ("Use espagnoles with fish stock.", True),
        ("Use fish stock.\n\nCompare with Espagnole.", True),
    ],
)
def test_a_mother_run_match_excludes_its_stated_derivative(body, binds):
    derivative = Preparation(
        title="LENTEN ESPAGNOLE",
        terms=(Term("LENTEN ESPAGNOLE", Language.FRENCH),),
        body=body,
        ref=SourceRef(source_id="test-1900", entry=24, line=24, fidelity=Fidelity.OCR),
        parent=None,
    )
    mother = ConceptId("espagnole")
    catalogue = Catalogue(
        witness=a_witness(fidelity=Fidelity.OCR),
        preparations=(derivative,),
        mothers=frozenset({mother}),
    )
    assert catalogue.matches(mother) == ((derivative,) if binds else ())
    assert catalogue.find(derivative.concept) == derivative
    assert replace(catalogue, mothers=frozenset()).find(mother) == derivative


@pytest.mark.corpus
def test_the_scan_does_not_promote_lenten_espagnole_to_mother(escoffier_1907):
    mother = ConceptId("espagnole")
    derivative = escoffier_1907.find(ConceptId("lenten-espagnole"))
    assert derivative is not None
    assert derivative.ref.entry == 24
    assert derivative.parent == mother
    assert escoffier_1907.find(mother) is None
    assert derivative in escoffier_1907.children_of(mother)
    assert escoffier_1907.children_of(derivative.concept) == ()


@pytest.mark.unit
def test_an_exact_mother_name_binds_before_the_guard_applies():
    base = Preparation(
        title="ESPAGNOLE",
        terms=(Term("ESPAGNOLE", Language.FRENCH),),
        body="Espagnole is finished with brown stock.",
        ref=SourceRef(source_id="test-1900", entry=22, line=22, fidelity=Fidelity.OCR),
        parent=None,
    )
    mother = ConceptId("espagnole")
    catalogue = Catalogue(
        witness=a_witness(fidelity=Fidelity.OCR),
        preparations=(base,),
        mothers=frozenset({mother}),
    )
    assert base.states(mother)
    assert catalogue.matches(mother) == (base,)
    assert catalogue.find(mother) == base
