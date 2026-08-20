"""Saucier: sauce preparations as structured, language-tagged records.

Reads a culinary source and returns a catalogue: what each preparation is
called, in which language, which mother it derives from, and the source line
the claim came from. No model runs. Every output is traceable to the text.

The package follows a hexagonal layout. The domain holds frozen entities and
performs no IO, ports declare the protocols adapters satisfy, services
orchestrate, and adapters touch the outside world. `lint-imports` enforces
those boundaries on every commit.

Attributes:
    __version__ (str): The released version. Updated by release-please, and
        checked against `pyproject.toml`, the release manifest, and `uv.lock`
        by `scripts/check_versions.py`.

Examples:
    Extract a catalogue from the committed source:

    ```python
    from saucier.infrastructure.bootstrap import escoffier_source
    from saucier.services.extraction import extract

    catalogue = extract(escoffier_source())
    unresolved = len(catalogue.preparations) - catalogue.resolved
    ```

See Also:
    - [saucier.domain][]: The entities every layer is written against.
    - [saucier.services.extraction][]: Where a source becomes a catalogue.
"""

__version__ = "0.3.0"  # x-release-please-version
