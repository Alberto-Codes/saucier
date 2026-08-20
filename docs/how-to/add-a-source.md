# Add a source

Point the extractor at a book other than Escoffier.

## Check the licence first

Only sources you may redistribute go in `corpus/`. Anything published in the
United States through 1930 is public domain, which covers most historical
cookbooks worth parsing. [Project Gutenberg](https://www.gutenberg.org/) texts
are already cleared, and carry a licence wrapper the reader strips
automatically.

If a source cannot be committed, it does not belong in `corpus/` — write a
fetch script instead, and keep the file untracked.

## Add the text

```console
$ curl -sL https://www.gutenberg.org/cache/epub/65061/pg65061.txt \
    -o corpus/farmer-1896.txt
```

## Register it

In `src/saucier/infrastructure/config.py`, add the identifier and give
`Paths` a property for it:

```python
FARMER = "farmer-1896"


@property
def farmer(self) -> Path:
    """The Fannie Farmer source text."""
    return self.corpus / f"{FARMER}.txt"
```

Then add a factory in `bootstrap.py`, returning the port rather than the
concrete class:

```python
def farmer_source(paths: Paths | None = None) -> SourceText:
    resolved = paths or Paths.discover()
    return GutenbergText(path=resolved.farmer, source_id=FARMER)
```

## Check whether the entry pattern fits

`extract` raises `NoPreparationsFound` when a source numbers its entries
differently. It raises the same error when the entries parse but none of them
is a sauce. Both are expected failures, not bugs. Escoffier's
`22—BROWN SAUCE OR ESPAGNOLE` form is specific to him.

```console
$ uv run python -c "
from saucier.infrastructure.bootstrap import farmer_source
from saucier.services.extraction import extract
print(len(extract(farmer_source()).preparations))
"
```

If that raises, the source needs its own `ENTRY` pattern. Do not loosen the
existing one to fit both. A looser pattern silently admits garbage from the
source it was already working on.

A source that does not divide itself into titled chapters has no sauce
chapter, so `sauce_chapters` returns nothing and only headings that say
"sauce" qualify. That resolves less, and it is right. See
[ADR-0007](../adr/0007-the-source-classifies-its-own-contents.md).

## For a non-Gutenberg source

Write a new driven adapter beside `gutenberg.py` satisfying `SourceText`: a
`source_id` property, a `line_offset` property, and a `lines()` method
returning body lines with the format's packaging removed. `line_offset` is
the count of file lines the adapter stripped before the body, so a recorded
line number names a line in the file. Nothing above the adapter layer
changes.
