"""The pure core: culinary terms, preparations, and the derivations between them.

Domain modules perform no IO — no file access, no JSON, no argument parsing.
They take plain data in and return plain data out, which keeps every rule in
this layer testable without a corpus on disk. The import-linter contracts in
`pyproject.toml` enforce that mechanically rather than by convention.

Attributes:
    types: Value objects — `Language`, `ConceptId`, and concept folding.
    models: Frozen entities — `Term`, `Preparation`, `SourceRef`, `Catalogue`.
    witness: What a text is — `Edition`, `Fidelity`, and `Witness`.
    errors: The typed exception hierarchy this package raises deliberately.

Examples:
    Build a language-tagged term and read its concept:

    ```python
    from saucier.domain.models import Term
    from saucier.domain.types import Language

    term = Term("Velouté", Language.FRENCH)
    assert term.concept == "veloute"
    ```

See Also:
    - [saucier.ports][]: The protocols this layer is consumed through.
"""
