"""Port for carrying catalogues across a process boundary.

A store is a place a catalogue is kept. An interchange is a representation
a catalogue travels in, so that a program with none of these classes can
read it. The two are different decisions, and ADR-0016 keeps them apart
with two ports rather than one.

The contract works on text, never on paths or on standard streams. The
writer yields lines and the reader consumes lines, so a test needs an
`io.StringIO` and the command line needs `sys.stdin` and `sys.stdout`,
and both go through the same code.

Examples:
    Carry every catalogue out and rebuild it from the lines:

    ```python
    lines = list(interchange.encode(catalogues))
    assert interchange.decode(lines) == tuple(catalogues)
    ```

See Also:
    - [saucier.adapters.driven.jsonl][]: The implementation in use.
    - [saucier.ports.store][]: The contract for keeping a catalogue.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Protocol

from saucier.domain.models import Catalogue


class CatalogueInterchange(Protocol):
    """A representation catalogues can be written to and rebuilt from.

    Examples:
        Round-trip through the contract rather than an implementation:

        ```python
        rebuilt = interchange.decode(interchange.encode([catalogue]))
        assert rebuilt == (catalogue,)
        ```
    """

    def encode(self, catalogues: Iterable[Catalogue]) -> Iterator[str]:
        """Render catalogues as lines of the interchange.

        Args:
            catalogues: The catalogues to carry, in the order to write them.

        Yields:
            One record per line, each ending in a newline.
        """
        ...

    def decode(self, lines: Iterable[str]) -> tuple[Catalogue, ...]:
        """Rebuild every catalogue the lines carry.

        The lines are consumed one at a time. The result arrives only when
        the stream ends, because a catalogue is validated whole.

        Args:
            lines: Lines of the interchange, in any order.

        Returns:
            The rebuilt catalogues, in the order their witness records appeared.

        Raises:
            RecordRejected: If any line is not a record this reader accepts,
                or the rebuilt catalogues violate a domain invariant.
        """
        ...
