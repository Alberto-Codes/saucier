"""Assembly root: the only layer that knows about every other layer.

Configuration and wiring live here so that no other module hardcodes a path
or picks an adapter. Everything above it receives its collaborators already
constructed.

Attributes:
    config: `Paths` and the corpus constants, including the URL and the
        citable origin each committed witness came from.
    bootstrap: Factory functions returning adapters typed as their ports.

Examples:
    Wire the default adapters and extract every committed witness:

    ```python
    from saucier.infrastructure.bootstrap import escoffier_sources
    from saucier.services.extraction import extract

    catalogues = [extract(source) for source in escoffier_sources()]
    ```

See Also:
    - [saucier.adapters][]: The implementations being wired.
"""
