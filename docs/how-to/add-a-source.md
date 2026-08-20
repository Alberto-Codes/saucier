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
differently. That is the expected failure, not a bug — Escoffier's
`22—BROWN SAUCE OR ESPAGNOLE` form is specific to him.

```console
$ uv run python -c "
from saucier.infrastructure.bootstrap import farmer_source
from saucier.services.extraction import extract
print(len(extract(farmer_source()).preparations))
"
```

If that raises, the source needs its own `ENTRY` pattern. Do not loosen the
existing one to fit both — a looser pattern silently admits garbage from the
source it was already working on.

## For a non-Gutenberg source

Write a new driven adapter beside `gutenberg.py` satisfying `SourceText`:
a `source_id` property and a `lines()` method returning body lines with the
format's packaging removed. Nothing above the adapter layer changes.
