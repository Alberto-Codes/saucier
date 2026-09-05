"""Orchestration: reading structure out of a source.

Services import ports and the domain, never adapters and never
infrastructure. They receive their collaborators already built, so the same
extraction runs against a Gutenberg ebook, a test fixture, or anything else
that satisfies `SourceText`.

Attributes:
    extraction: Deterministic extraction of preparations from a numbered
        source, with no model involved.
    front_matter: Reading the edition a source states about itself.
    comparison: Comparing two catalogues, with a cause on every row.
    procedure: Fetching a recorded procedure and checking every word of
        it against the body it cites.

Examples:
    Extract a catalogue from any source implementation:

    ```python
    from saucier.services.extraction import extract

    catalogue = extract(source)
    print(len(catalogue.preparations), catalogue.resolved)
    ```

See Also:
    - [saucier.ports][]: The contracts a source must satisfy.
"""
