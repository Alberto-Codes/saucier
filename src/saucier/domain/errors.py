"""Typed exception hierarchy for the domain.

Every error this package raises deliberately descends from `SaucierError`,
so an entry point can turn intended failures into an exit code while letting
genuine bugs surface as tracebacks.

Examples:
    Catch anything this package raises on purpose:

    ```python
    from saucier.domain.errors import SaucierError

    try:
        catalogue = store.load("escoffier-1907")
    except SaucierError as exc:
        print(f"saucier: {exc}")
    ```

See Also:
    - [saucier.adapters.driving.cli][]: Where these become exit codes.
"""

from __future__ import annotations


class SaucierError(Exception):
    """Base class for every error this package raises deliberately.

    Examples:
        Distinguish intended failures from bugs:

        ```python
        try:
            run()
        except SaucierError:
            ...  # expected; report and exit
        ```
    """


class SourceUnreadable(SaucierError):
    """A source text could not be read or did not have the expected shape.

    Examples:
        Raised when the corpus file is absent:

        ```python
        source.lines()  # SourceUnreadable: cannot read source at ...
        ```
    """


class NoPreparationsFound(SaucierError):
    """A source parsed cleanly but yielded no preparations.

    Almost always means the entry pattern does not match this source, rather
    than that the source is empty.

    Examples:
        Raised when a source numbers its entries some other way:

        ```python
        extract(source)  # NoPreparationsFound: no numbered entries in ...
        ```
    """
