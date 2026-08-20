"""Assembly root: the only layer that knows about every other layer.

Configuration and wiring live here so that no other module hardcodes a path
or picks an adapter. Everything above it receives its collaborators already
constructed.

Attributes:
    config: `Paths` and the corpus constants, including the source URL the
        committed text came from.
    bootstrap: Factory functions returning adapters typed as their ports.

Examples:
    Wire the default adapters and run an extraction:

    ```python
    from saucier.infrastructure.bootstrap import escoffier_source
    from saucier.services.extraction import extract

    catalogue = extract(escoffier_source())
    ```

See Also:
    - [saucier.adapters][]: The implementations being wired.
"""
