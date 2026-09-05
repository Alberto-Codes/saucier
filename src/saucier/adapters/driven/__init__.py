"""Driven adapters: implementations the application calls out to.

Each module here satisfies one port. Swapping JSON for SQLite means adding a
module beside `json_store` and changing one line in the assembly root, with
no service or domain code touched.

Attributes:
    gutenberg: `GutenbergText`, reading a Project Gutenberg ebook with its
        licence wrapper stripped.
    plain_text: `PlainText`, reading a file that carries no wrapper at all.
    normalised: `NormalisedText`, wrapping any source to clean the whitespace
        a scanner leaves behind.
    json_store: `JsonCatalogueStore`, persisting catalogues as JSON files.
    jsonl: `JsonlInterchange`, carrying catalogues as one record per line
        so a program with none of these classes can read them.
    jsonl_records: The `saucier/1` record schema and the strict reader
        that enforces it, line by line.
    hand_procedures: `HandProcedures`, the procedures recorded by hand,
        one per witness of Mornay, looked up by reference.

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
