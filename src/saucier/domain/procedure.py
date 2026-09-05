"""What a body states is done: a procedure, in the witness's own words.

A preparation records one parent and says nothing of what is done with it.
The body says. `MORNAY SAUCE` boils one pint of Béchamel with one-quarter
pint of fumet, reduces by a good quarter, and adds two oz. each of two
cheeses. A procedure holds those operations in the order the body states
them, and every element quotes the words it was read from.

The entities refuse a state the witness could not produce. An input whose
term is not among its words, an operation whose input is not inside its
clause, and a parameter whose unit is not among its words are all refused
at construction. A procedure can then say which of its operations a body
does not carry, so a procedure recorded by hand is checked against the
text it cites rather than trusted.

A number the words do not give is unresolved. `a few minutes` records
`minutes` and no number, and no code fills one in. ADR-0002 governs that
slot as it governs a parent.

Examples:
    Record one operation and check it against the clause it quotes:

    ```python
    from fractions import Fraction

    from saucier.domain.models import Term
    from saucier.domain.procedure import Input, Operation, Parameter, Procedure
    from saucier.domain.types import Language

    boil = Operation(
        wording="Boil one pint of Béchamel Sauce",
        verb=Term("Boil", Language.ENGLISH),
        inputs=(
            Input(
                wording="one pint of Béchamel Sauce",
                term=Term("Béchamel Sauce", Language.FRENCH),
                quantity=Parameter(wording="one pint", number=Fraction(1), unit="pint"),
            ),
        ),
        instrument=None,
        criterion=None,
        duration=None,
        constraints=(),
    )
    assert Procedure((boil,)).unstated("Boil one pint of Béchamel Sauce.") == ()
    ```

See Also:
    - [saucier.domain.models][]: The preparation a procedure sits beside.
    - [saucier.services.procedure][]: What checks a recorded procedure
      against the body it cites.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from saucier.domain.models import Term


def collapse(text: str) -> str:
    """Fold every run of whitespace to one space, so wrapped lines compare.

    A body wraps at the column, a scan double-spaces its words, and the
    transcription sets a non-breaking space before `oz.`. None of that is
    a word, so none of it takes part in a comparison.

    Args:
        text: Words from a witness, or quoted from one.

    Returns:
        The same words separated by single spaces, with none at either end.
    """
    return " ".join(text.split())


def _within(part: str, whole: str) -> bool:
    """Test whether one run of words lies inside another.

    Args:
        part: The words that should be quoted.
        whole: The words they should be quoted from.

    Returns:
        True if `part` appears in `whole` once whitespace is collapsed.
    """
    return collapse(part) in collapse(whole)


def _quoted(part: str, whole: str, what: str) -> None:
    """Refuse an element whose words are not inside the words it was read from.

    Args:
        part: The words the element carries.
        whole: The words it claims to be read from.
        what: What the element is, for the message.

    Raises:
        ValueError: If `part` is not inside `whole`.
    """
    if not _within(part, whole):
        msg = f"{what} {part!r} is not inside {whole!r}"
        raise ValueError(msg)


@dataclass(frozen=True, slots=True, kw_only=True)
class Parameter:
    """Words that state how much, how long, or how far, and the number they give.

    Keyword-only, because the number and the unit are read out of the
    wording and a reader checks them against it. `one-quarter pint` gives
    `1/4` and `pint`. `a few minutes` gives no number, and the slot stays
    `None` rather than being filled with a guess.

    Attributes:
        wording (str): The words, as the witness writes them.
        number (Fraction | None): The number the words give. `None` when
            they give none, which is unresolved and never zero.
        unit (str | None): The unit the words name, or `None` when they
            name none.

    Examples:
        A stated duration with no number stays unresolved:

        ```python
        few = Parameter(wording="a few minutes", number=None, unit="minutes")
        assert few.number is None
        ```
    """

    wording: str
    number: Fraction | None
    unit: str | None

    def __post_init__(self) -> None:
        """Refuse a parameter with no words, or a unit its words do not name.

        Raises:
            ValueError: If the wording is blank, or the unit is not among
                the words.
        """
        if not self.wording.strip():
            msg = "a parameter needs its wording"
            raise ValueError(msg)
        if self.unit is not None:
            _quoted(self.unit, self.wording, "unit")


@dataclass(frozen=True, slots=True, kw_only=True)
class Input:
    """One thing an operation takes, as the witness names it.

    The preparation in progress is not an input. `Finish the sauce with
    two oz. of butter` takes butter, and `the sauce` is what is being made.

    Attributes:
        wording (str): The words the input was read from, quantity included.
        term (Term): What is taken, language-tagged and never translated.
        quantity (Parameter | None): How much, or `None` when the words
            state no quantity.

    Examples:
        An input carries its term and its quantity inside its own words:

        ```python
        butter = Input(
            wording="two oz. of butter",
            term=Term("butter", Language.ENGLISH),
            quantity=Parameter(wording="two oz.", number=Fraction(2), unit="oz."),
        )
        assert butter.term.concept == "butter"
        ```
    """

    wording: str
    term: Term
    quantity: Parameter | None

    def __post_init__(self) -> None:
        """Refuse an input whose term or quantity is not among its words.

        Raises:
            ValueError: If the term's surface or the quantity's wording is
                not inside the input's wording.
        """
        _quoted(self.term.surface, self.wording, "term")
        if self.quantity is not None:
            _quoted(self.quantity.wording, self.wording, "quantity")


@dataclass(frozen=True, slots=True, kw_only=True)
class Operation:
    """One action the body states, with everything the same clause states.

    Every field is read from `wording`, and the entity refuses one that is
    not. No field carries a default, for the reason `Preparation.parent`
    carries none: an absence is stated at every construction site rather
    than inherited.

    Attributes:
        wording (str): The clause, as the witness writes it.
        verb (Term): The action, as a term. `Boil` is English and folds to
            `boil`.
        inputs (tuple[Input, ...]): What the operation takes, in the order
            the clause states them.
        instrument (Term | None): The tool the clause names, or `None`.
        criterion (Parameter | None): What the operation is carried to, or
            `None` when the clause states none.
        duration (Parameter | None): How long, or `None` when the clause
            states no duration.
        constraints (tuple[str, ...]): Conditions the clause sets, in its
            own words.

    Examples:
        A reduction states a criterion and nothing else:

        ```python
        reduce = Operation(
            wording="Reduce by a good quarter",
            verb=Term("Reduce", Language.ENGLISH),
            inputs=(),
            instrument=None,
            criterion=Parameter(wording="by a good quarter", number=None, unit=None),
            duration=None,
            constraints=(),
        )
        assert reduce.criterion.number is None
        ```
    """

    wording: str
    verb: Term
    inputs: tuple[Input, ...]
    instrument: Term | None
    criterion: Parameter | None
    duration: Parameter | None
    constraints: tuple[str, ...]

    def __post_init__(self) -> None:
        """Refuse an operation carrying words its clause does not.

        Raises:
            ValueError: If the verb, an input, the instrument, the
                criterion, the duration, or a constraint is not inside the
                wording.
        """
        for what, words in self._elements():
            _quoted(words, self.wording, what)

    def _elements(self) -> tuple[tuple[str, str], ...]:
        """List every run of words this operation claims to quote.

        Returns:
            Pairs of what an element is and the words it carries.
        """
        named = [("verb", self.verb.surface)]
        named.extend(("input", found.wording) for found in self.inputs)
        if self.instrument is not None:
            named.append(("instrument", self.instrument.surface))
        if self.criterion is not None:
            named.append(("criterion", self.criterion.wording))
        if self.duration is not None:
            named.append(("duration", self.duration.wording))
        named.extend(("constraint", words) for words in self.constraints)
        return tuple(named)


@dataclass(frozen=True, slots=True)
class Procedure:
    """The operations one body states, in the order it states them.

    Attributes:
        operations (tuple[Operation, ...]): The operations, in body order.
            At least one, because `None` already says nothing was recorded
            and a procedure that states nothing would say it twice.

    Examples:
        Ask a procedure what a body fails to state:

        ```python
        assert Procedure((reduce,)).unstated("Strain the sauce.") == (
            "Reduce by a good quarter",
        )
        ```
    """

    operations: tuple[Operation, ...]

    def __post_init__(self) -> None:
        """Refuse a procedure with no operations.

        Raises:
            ValueError: If no operation was given.
        """
        if not self.operations:
            msg = "a procedure needs at least one operation"
            raise ValueError(msg)

    def unstated(self, body: str) -> tuple[str, ...]:
        """Name every operation whose words the body does not carry, in order.

        Each operation is looked for after the one before it, so an
        operation the body states out of order is reported as unstated.
        Whitespace is collapsed on both sides, so a clause that wraps in
        the body is found from a wording written on one line.

        Args:
            body: The entry's prose, verbatim.

        Returns:
            The wording of each operation not found, in procedure order.
            Empty when the body states every operation in that order.
        """
        text = collapse(body)
        cursor = 0
        missing: list[str] = []
        for operation in self.operations:
            words = collapse(operation.wording)
            found = text.find(words, cursor)
            if found < 0:
                missing.append(operation.wording)
            else:
                cursor = found + len(words)
        return tuple(missing)
