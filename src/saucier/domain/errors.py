"""Typed exception hierarchy for the domain.

Every error this package raises deliberately descends from `SaucierError`,
so an entry point can turn intended failures into an exit code while letting
genuine bugs surface as tracebacks. That rule covers bad input of every
kind: an unreadable source, a damaged store, a rejected record of the
interchange, an unfoldable term, and a tree with no corpus in it.

Examples:
    Catch anything this package raises on purpose:

    ```python
    from saucier.domain.errors import SaucierError

    try:
        catalogue = store.load("escoffier-1909")
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


class EditionUnstated(SaucierError):
    """A source's front matter names neither an edition nor a copyright year.

    A document with no stated identity is a situation to report. Falling back
    to the filename is what ADR-0009 exists to forbid.

    Examples:
        Raised when the head of a file carries no printing history:

        ```python
        read_edition(lines)  # EditionUnstated: no edition and no ...
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


class UnfoldableTerm(SaucierError, ValueError):
    """A surface form carries no letters or digits to fold into a concept id.

    Subclasses `ValueError` as well, because folding is a value operation and
    a caller may reasonably catch either.

    Examples:
        Raised when a heading is punctuation only:

        ```python
        to_concept_id("***")  # UnfoldableTerm: surface form yields ...
        ```
    """


class CatalogueUnwritable(SaucierError):
    """A catalogue could not be written to its store.

    Examples:
        Raised when the output directory rejects the write:

        ```python
        store.save(catalogue)  # CatalogueUnwritable: cannot write ...
        ```
    """


class RecordRejected(SaucierError):
    """A line of the interchange is not a record this reader accepts.

    The message names the line, so a reader can open the stream at the
    failure. Malformed JSON, an unknown schema or type, a duplicate id, a
    field the schema does not name, and a preparation whose witness the
    stream never carries all arrive here.

    Examples:
        Raised with the failing line number first:

        ```python
        interchange.decode(lines)  # RecordRejected: line 7: duplicate id ...
        ```
    """


class ProjectRootNotFound(SaucierError):
    """No ancestor directory holds `corpus/`, so the layout is unknown.

    Examples:
        Raised when saucier runs outside a working tree:

        ```python
        Paths.discover()  # ProjectRootNotFound: no corpus/ directory ...
        ```
    """
