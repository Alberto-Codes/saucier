"""Procedures recorded by hand, one per witness of one preparation.

`MORNAY SAUCE` is entry 91. This module holds its procedure twice, once
in the words of the 1909 transcription and once in the words of the 1907
scan, each keyed by the reference the catalogue records for it. The
service checks every wording against the body before it is shown, so a
literal here that misquotes its witness is refused rather than printed.

The scan is quoted as the scan reads. Its Béchamel is `Bdchamel`, its
Gruyère is `Gruy^re`, and its reduce operation carries the running header
of page 40, because the sentence crosses a page break and the header sits
inside it. The last three operations read the same in both witnesses,
word for word, and are held once, as is the `two oz.` quantity that three
inputs share. ADR-0017 records why none of the damage is repaired here.

Examples:
    Look up what is recorded for a reference:

    ```python
    from saucier.adapters.driven.hand_procedures import HandProcedures

    procedure = HandProcedures().at(preparation.ref)
    ```

See Also:
    - [saucier.ports.procedure][]: The contract this satisfies.
    - [saucier.services.procedure][]: What checks a procedure against its
      body.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction

from saucier.domain.models import SourceRef, Term
from saucier.domain.procedure import Input, Operation, Parameter, Procedure
from saucier.domain.types import Language
from saucier.domain.witness import Fidelity

HAND = "hand"
"""Who recorded every procedure in this module."""

REVISION = SourceRef(
    source_id="escoffier-1909", entry=91, line=2437, fidelity=Fidelity.TRANSCRIPTION
)
"""Where the 1909 transcription states Mornay."""

SCAN = SourceRef(source_id="escoffier-1907", entry=91, line=2864, fidelity=Fidelity.OCR)
"""Where the 1907 scan states Mornay. Its heading reads `MORN AY SAUCE`."""

TWO_OUNCES = Parameter(wording="two oz.", number=Fraction(2), unit="oz.")
"""The quantity three inputs share, in the words both witnesses use."""


def _boil(wording: str, bechamel: str, fumet: str) -> Operation:
    """Build the first operation, which differs between the witnesses.

    Both inputs state a quantity in pints, and each is built in place.

    Args:
        wording: The whole clause, as the witness writes it.
        bechamel: The surface form of Béchamel in that witness.
        fumet: The words of the fumet input in that witness.

    Returns:
        The operation.
    """
    return Operation(
        wording=wording,
        verb=Term("Boil", Language.ENGLISH),
        inputs=(
            Input(
                wording=f"one pint of {bechamel}",
                term=Term(bechamel, Language.FRENCH),
                quantity=Parameter(wording="one pint", number=Fraction(1), unit="pint"),
            ),
            Input(
                wording=fumet,
                term=Term("fumet", Language.FRENCH),
                quantity=Parameter(
                    wording="one-quarter pint", number=Fraction(1, 4), unit="pint"
                ),
            ),
        ),
        instrument=None,
        criterion=None,
        duration=None,
        constraints=(),
    )


def _reduce(wording: str) -> Operation:
    """Build the second operation, whose clause the scan interrupts.

    Args:
        wording: The clause, as the witness writes it.

    Returns:
        The operation.
    """
    return Operation(
        wording=wording,
        verb=Term("Reduce", Language.ENGLISH),
        inputs=(),
        instrument=None,
        criterion=Parameter(wording="by a good quarter", number=None, unit=None),
        duration=None,
        constraints=(),
    )


def _add(gruyere: str) -> Operation:
    """Build the third operation, whose Gruyère the scan misreads.

    Both cheeses take `TWO_OUNCES`, the quantity the clause states twice.

    Args:
        gruyere: The surface form of Gruyère in that witness.

    Returns:
        The operation.
    """
    return Operation(
        wording=f"add two oz. of {gruyere} and two oz. of grated Parmesan",
        verb=Term("add", Language.ENGLISH),
        inputs=(
            Input(
                wording=f"two oz. of {gruyere}",
                term=Term(gruyere, Language.FRENCH),
                quantity=TWO_OUNCES,
            ),
            Input(
                wording="two oz. of grated Parmesan",
                term=Term("Parmesan", Language.ENGLISH),
                quantity=TWO_OUNCES,
            ),
        ),
        instrument=None,
        criterion=None,
        duration=None,
        constraints=(),
    )


RETURN_TO_FIRE = Operation(
    wording="Put the sauce on the fire again for a few minutes",
    verb=Term("Put", Language.ENGLISH),
    inputs=(),
    instrument=None,
    criterion=None,
    duration=Parameter(wording="a few minutes", number=None, unit="minutes"),
    constraints=("on the fire again",),
)
"""The fourth operation. The text names no number of minutes."""

STIR = Operation(
    wording="ensure the melting of the cheese by stirring with a small whisk",
    verb=Term("stirring", Language.ENGLISH),
    inputs=(),
    instrument=Term("small whisk", Language.ENGLISH),
    criterion=Parameter(wording="the melting of the cheese", number=None, unit=None),
    duration=None,
    constraints=(),
)
"""The fifth operation. The cook stirs, and the melting is the criterion."""

FINISH = Operation(
    wording="Finish the sauce away from the fire with two oz. of butter added by degrees",
    verb=Term("Finish", Language.ENGLISH),
    inputs=(
        Input(
            wording="two oz. of butter",
            term=Term("butter", Language.ENGLISH),
            quantity=TWO_OUNCES,
        ),
    ),
    instrument=None,
    criterion=None,
    duration=None,
    constraints=("away from the fire", "added by degrees"),
)
"""The sixth operation, with the one stated constraint the post names."""

MORNAY_1909 = Procedure(
    (
        _boil(
            "Boil one pint of Béchamel Sauce with one-quarter pint of the _fumet_ "
            "of the fish, poultry, or vegetable, which is to constitute the dish",
            "Béchamel Sauce",
            "one-quarter pint of the _fumet_ of the fish, poultry, or vegetable, "
            "which is to constitute the dish",
        ),
        _reduce("Reduce by a good quarter"),
        _add("Gruyère"),
        RETURN_TO_FIRE,
        STIR,
        FINISH,
    )
)
"""Mornay as the 1909 transcription states it, at line 2437.

The underscores around `fumet` are the transcription's italics, kept
because the wording quotes the witness.
"""

MORNAY_1907 = Procedure(
    (
        _boil(
            "Boil one pint of Bdchamel Sauce with one-quarter pint of the fumet "
            "of that fish which is to constitute the dish",
            "Bdchamel Sauce",
            "one-quarter pint of the fumet of that fish which is to constitute the dish",
        ),
        _reduce("Reduce 40 GUIDE TO MODERN COOKERY by a good quarter"),
        _add("Gruy^re"),
        RETURN_TO_FIRE,
        STIR,
        FINISH,
    )
)
"""Mornay as the 1907 scan states it, at line 2864.

The fumet is of `that fish`, where the revision writes `the fish, poultry,
or vegetable`. That is the first editorial difference between the two
printings this project has confirmed.
"""

MORNAY: Mapping[SourceRef, Procedure] = {REVISION: MORNAY_1909, SCAN: MORNAY_1907}
"""Every procedure recorded by hand, keyed by the reference it was read at."""


class HandProcedures:
    """Procedures recorded by hand, looked up by reference.

    Serves `MORNAY`, the two procedures this module holds, and nothing
    else. A caller that needs other procedures stands behind the port
    with its own adapter.

    Examples:
        The scan's Mornay is found by its reference, not by its damaged name:

        ```python
        assert HandProcedures().at(SCAN) is MORNAY_1907
        ```
    """

    @property
    def recorder(self) -> str:
        """Who recorded these procedures.

        Returns:
            `hand`.
        """
        return HAND

    def at(self, ref: SourceRef) -> Procedure | None:
        """Look up the procedure recorded at one reference.

        Args:
            ref: Where the preparation was found.

        Returns:
            The procedure `MORNAY` holds for that reference, or `None` when
            it holds none.
        """
        return MORNAY.get(ref)
