"""Driven adapters: implementations the application calls out to.

Each module here satisfies one port. Swapping JSON for SQLite means adding a
module beside `json_store` and changing one line in the assembly root, with
no service or domain code touched.

Attributes:
    gutenberg: `GutenbergText`, reading a Project Gutenberg ebook with its
        licence wrapper stripped.
    json_store: `JsonCatalogueStore`, persisting catalogues as JSON files.

Examples:
    Persist a catalogue to a directory:

    ```python
    from pathlib import Path

    from saucier.adapters.driven.json_store import JsonCatalogueStore

    JsonCatalogueStore(Path("data")).save(catalogue)
    ```

See Also:
    - [saucier.ports][]: The contracts these modules satisfy.
"""
