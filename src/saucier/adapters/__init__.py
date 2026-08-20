"""Adapters: everything that touches the world outside the hexagon.

Driven adapters implement ports and are called by the application. Driving
adapters are entry points and call into it. Neither is imported by the
domain or by a service; the assembly root wires them in.

Attributes:
    driven: Implementations of ports — source readers and catalogue stores.
    driving: Entry points — the command line interface.

Examples:
    Read the committed corpus through a driven adapter:

    ```python
    from pathlib import Path

    from saucier.adapters.driven.gutenberg import GutenbergText

    source = GutenbergText(Path("corpus/escoffier-1907.txt"), "escoffier-1907")
    ```

See Also:
    - [saucier.infrastructure][]: Where adapters are chosen and wired.
"""
