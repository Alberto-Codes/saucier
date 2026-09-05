"""Fetching a recorded procedure and checking it against the body it cites.

A procedure is recorded beside a preparation, and this release records
one by hand. A hand can misquote. So a recorded procedure is never shown
until every operation it carries has been found in the body, in order.
One that fails is reported as damage, the way a stored file that will not
parse is reported, rather than printed as if the text said it.

Examples:
    Fetch the procedure for a preparation, or learn that none is recorded:

    ```python
    from saucier.services.procedure import procedure_of

    procedure = procedure_of(preparation, recorded)
    if procedure is None:
        print(f"{preparation.title} is unrecorded")
    ```

See Also:
    - [saucier.domain.procedure][]: The entities and the check itself.
    - [saucier.ports.procedure][]: Where a recorded procedure comes from.
"""

from __future__ import annotations

from saucier.domain.errors import ProcedureUnstated
from saucier.domain.models import Preparation
from saucier.domain.procedure import Procedure
from saucier.ports.procedure import RecordedProcedures


def procedure_of(
    preparation: Preparation, recorded: RecordedProcedures
) -> Procedure | None:
    """Fetch the procedure recorded for a preparation, checked against its body.

    Args:
        preparation: The preparation to look up.
        recorded: Where recorded procedures come from.

    Returns:
        The recorded procedure, or `None` when the preparation is
        unrecorded. `None` never means the source states no procedure.

    Raises:
        ProcedureUnstated: If the body does not state every operation of
            the recorded procedure, in the order recorded. The message
            names the first operation not found.
    """
    procedure = recorded.at(preparation.ref)
    if procedure is None:
        return None
    missing = procedure.unstated(preparation.body)
    if missing:
        ref = preparation.ref
        msg = (
            f"{preparation.title} at line {ref.line} of {ref.source_id} "
            f"does not state {missing[0]!r}"
        )
        raise ProcedureUnstated(msg)
    return procedure
