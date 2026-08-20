"""Ports: the protocols adapters satisfy.

Ports are structural (`typing.Protocol`), so an adapter implements one by
shape rather than by inheritance. They import the domain and nothing else,
which is what lets a service be written against a contract instead of a
concrete reader or store.

Attributes:
    source: `SourceText`, a readable source document with its packaging
        already stripped.
    store: `CatalogueStore`, somewhere an extracted catalogue persists.

Examples:
    Type a function against the port rather than the adapter:

    ```python
    from saucier.ports.source import SourceText


    def count_lines(source: SourceText) -> int:
        return len(source.lines())
    ```

See Also:
    - [saucier.adapters][]: The implementations.
"""
