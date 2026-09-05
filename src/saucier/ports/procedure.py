"""Port for looking up the procedure recorded for a preparation.

A procedure is recorded beside a preparation, and this release records
one by hand. Where a recorded procedure comes from is an adapter's
concern, so that a rule reader or a model reader can stand behind the
same contract and name itself. The lookup is by reference, because a
reference names one heading line of one witness and a title does not.

Examples:
    Fetch what is recorded for a preparation:

    ```python
    procedure = recorded.at(preparation.ref)
    if procedure is None:
        print(f"{preparation.title} is unrecorded")
    ```

See Also:
    - [saucier.adapters.driven.hand_procedures][]: The implementation in use.
    - [saucier.services.procedure][]: What checks the answer against the
      body it cites.
"""

from __future__ import annotations

from typing import Protocol

from saucier.domain.models import SourceRef
from saucier.domain.procedure import Procedure


class RecordedProcedures(Protocol):
    """Somewhere a recorded procedure can be looked up by its reference.

    Examples:
        Ask through the contract rather than an implementation:

        ```python
        assert recorded.recorder == "hand"
        procedure = recorded.at(preparation.ref)
        ```
    """

    @property
    def recorder(self) -> str:
        """Who recorded the procedures this port serves.

        `hand` in this release. A rule reader or a model names itself here,
        so a procedure is never shown without saying who read it.
        """
        ...

    def at(self, ref: SourceRef) -> Procedure | None:
        """Look up the procedure recorded at one reference.

        Args:
            ref: Where the preparation was found.

        Returns:
            The procedure recorded at that reference, or `None` when none
            is recorded there. `None` means unrecorded, never that the
            source states no procedure.
        """
        ...
