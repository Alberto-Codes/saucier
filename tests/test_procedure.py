"""The procedure entities, the check against a body, and the hand adapter.

A procedure quotes its witness. Every test here that builds an element
with words its clause does not carry expects a refusal, and every test
that checks a procedure against a body expects the unstated operations
named in order.
"""

from fractions import Fraction

import pytest
from conftest import a_witness

from saucier.adapters.driven.hand_procedures import (
    HAND,
    MORNAY_1907,
    MORNAY_1909,
    REVISION,
    SCAN,
    HandProcedures,
)
from saucier.domain.errors import ProcedureUnstated
from saucier.domain.models import Preparation, SourceRef, Term
from saucier.domain.procedure import Input, Operation, Parameter, Procedure, collapse
from saucier.domain.types import Language
from saucier.services.procedure import procedure_of

EN, FR = Language.ENGLISH, Language.FRENCH
WITNESS = a_witness()


def operation(wording, verb, **fields):
    """Build an operation stating nothing but what the test names."""
    given = {
        "inputs": (),
        "instrument": None,
        "criterion": None,
        "duration": None,
        "constraints": (),
    }
    given.update(fields)
    return Operation(wording=wording, verb=Term(verb, EN), **given)


PINT = Parameter(wording="one pint", number=Fraction(1), unit="pint")
BECHAMEL = Input(
    wording="one pint of Béchamel Sauce",
    term=Term("Béchamel Sauce", FR),
    quantity=PINT,
)
BOIL = operation("Boil one pint of Béchamel Sauce", "Boil", inputs=(BECHAMEL,))
REDUCE = operation(
    "Reduce by a good quarter",
    "Reduce",
    criterion=Parameter(wording="by a good quarter", number=None, unit=None),
)
STRAIN = operation("Strain the sauce", "Strain")
BODY = "Boil one pint of Béchamel Sauce.\nReduce by a good quarter, and serve."


class Recorded:
    """A port of the smallest shape, holding whatever a test hands it."""

    recorder = "test"

    def __init__(self, held):
        """Hold procedures keyed by reference."""
        self.held = held

    def at(self, ref):
        return self.held.get(ref)


def a_preparation(body, line=10):
    return Preparation(
        title="A SAUCE",
        terms=(Term("A SAUCE", EN),),
        body=body,
        ref=SourceRef(
            source_id=WITNESS.source_id,
            entry=1,
            line=line,
            fidelity=WITNESS.fidelity,
        ),
        parent=None,
    )


# --------------------------------------------------------------------------- #
# Parameters, inputs, and operations quote their words
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_a_parameter_records_the_number_and_unit_its_words_give():
    assert (PINT.number, PINT.unit) == (1, "pint")
    quarter = Parameter(wording="one-quarter pint", number=Fraction(1, 4), unit="pint")
    assert quarter.number == Fraction(1, 4)


@pytest.mark.unit
def test_a_parameter_with_no_number_is_unresolved_not_zero():
    few = Parameter(wording="a few minutes", number=None, unit="minutes")
    assert few.number is None
    assert few.unit == "minutes"


@pytest.mark.unit
def test_a_parameter_refuses_a_unit_its_words_do_not_name():
    with pytest.raises(ValueError, match="unit 'pint' is not inside"):
        Parameter(wording="two oz.", number=Fraction(2), unit="pint")


@pytest.mark.unit
def test_a_parameter_needs_its_wording():
    with pytest.raises(ValueError, match="needs its wording"):
        Parameter(wording="  ", number=None, unit=None)


@pytest.mark.unit
def test_an_input_refuses_a_term_outside_its_words():
    with pytest.raises(ValueError, match="term 'butter' is not inside"):
        Input(
            wording="one pint of Béchamel Sauce", term=Term("butter", EN), quantity=None
        )


@pytest.mark.unit
def test_an_input_refuses_a_quantity_outside_its_words():
    with pytest.raises(ValueError, match="quantity 'one pint' is not inside"):
        Input(wording="two oz. of butter", term=Term("butter", EN), quantity=PINT)


@pytest.mark.unit
def test_an_operation_refuses_a_verb_outside_its_clause():
    with pytest.raises(ValueError, match="verb 'Strain' is not inside"):
        operation("Reduce by a good quarter", "Strain")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("what", "fields"),
    [
        ("input", {"inputs": (BECHAMEL,)}),
        ("instrument", {"instrument": Term("small whisk", EN)}),
        (
            "criterion",
            {"criterion": Parameter(wording="until it coats", number=None, unit=None)},
        ),
        (
            "duration",
            {
                "duration": Parameter(
                    wording="a few minutes", number=None, unit="minutes"
                )
            },
        ),
        ("constraint", {"constraints": ("away from the fire",)}),
    ],
)
def test_an_operation_refuses_an_element_outside_its_clause(what, fields):
    with pytest.raises(ValueError, match=f"{what} .* is not inside"):
        operation("Reduce by a good quarter", "Reduce", **fields)


@pytest.mark.unit
def test_an_absence_is_stated_at_every_construction_site():
    """No field of an operation carries a default, as `parent` carries none."""
    with pytest.raises(TypeError):
        Operation(  # ty: ignore[missing-argument]
            wording="Reduce by a good quarter", verb=Term("Reduce", EN)
        )


@pytest.mark.unit
def test_a_procedure_needs_at_least_one_operation():
    with pytest.raises(ValueError, match="at least one operation"):
        Procedure(())


# --------------------------------------------------------------------------- #
# The check against a body
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_a_body_stating_every_operation_in_order_leaves_nothing_unstated():
    assert Procedure((BOIL, REDUCE)).unstated(BODY) == ()


@pytest.mark.unit
def test_an_operation_the_body_does_not_state_is_named():
    assert Procedure((BOIL, STRAIN, REDUCE)).unstated(BODY) == ("Strain the sauce",)


@pytest.mark.unit
def test_an_operation_stated_out_of_order_is_unstated():
    """Each operation is looked for after the one before it."""
    assert Procedure((REDUCE, BOIL)).unstated(BODY) == (
        "Boil one pint of Béchamel Sauce",
    )


@pytest.mark.unit
def test_wrapped_lines_and_non_breaking_spaces_do_not_hide_a_statement():
    """The 1909 text sets a no-break space before `oz.` and wraps at the column."""
    assert collapse("two\u00a0oz.\nof  butter ") == "two oz. of butter"
    butter = operation("Finish with two oz. of butter", "Finish")
    body = "Finish with two\u00a0oz.\nof butter added by degrees."
    assert Procedure((butter,)).unstated(body) == ()


# --------------------------------------------------------------------------- #
# The service and the hand adapter
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_an_unrecorded_preparation_yields_none():
    assert procedure_of(a_preparation(BODY), Recorded({})) is None


@pytest.mark.unit
def test_a_recorded_procedure_the_body_states_is_returned():
    preparation = a_preparation(BODY)
    procedure = Procedure((BOIL, REDUCE))
    assert (
        procedure_of(preparation, Recorded({preparation.ref: procedure})) is procedure
    )


@pytest.mark.unit
def test_a_recorded_procedure_the_body_does_not_state_is_damage():
    preparation = a_preparation(BODY)
    recorded = Recorded({preparation.ref: Procedure((BOIL, STRAIN))})
    with pytest.raises(
        ProcedureUnstated, match=r"line 10 .* does not state 'Strain the sauce'"
    ):
        procedure_of(preparation, recorded)


@pytest.mark.unit
def test_the_hand_adapter_names_itself():
    assert HandProcedures().recorder == HAND == "hand"


@pytest.mark.unit
def test_the_hand_adapter_answers_by_reference_not_by_name():
    """The scan's heading reads `MORN AY SAUCE`. The line finds it anyway."""
    recorded = HandProcedures()
    assert recorded.at(REVISION) is MORNAY_1909
    assert recorded.at(SCAN) is MORNAY_1907
    elsewhere = SourceRef(
        source_id=SCAN.source_id, entry=91, line=1, fidelity=SCAN.fidelity
    )
    assert recorded.at(elsewhere) is None


@pytest.mark.unit
def test_both_hand_procedures_state_six_verbs_in_one_order():
    verbs = ["boil", "reduce", "add", "put", "stirring", "finish"]
    for procedure in (MORNAY_1909, MORNAY_1907):
        assert [op.verb.concept for op in procedure.operations] == verbs
