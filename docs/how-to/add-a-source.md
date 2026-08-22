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

In `src/saucier/infrastructure/config.py`, add the work name, the origin, and
a `Paths` property for the file:

```python
FARMER = "farmer"
FARMER_ORIGIN = "Project Gutenberg 65061"


@property
def farmer(self) -> Path:
    """The Fannie Farmer source text."""
    return self.corpus / "farmer-1896.txt"
```

The work name has no year in it. The edition year is read from the
document's front matter, and the two together make the `source_id`. See
[ADR-0009](../adr/0009-the-source-states-its-own-identity.md).

Then add a factory in `bootstrap.py`, returning the port rather than the
concrete class:

```python
def farmer_source(paths: Paths | None = None) -> SourceText:
    resolved = paths or Paths.discover()
    return GutenbergText(
        path=resolved.farmer,
        work=FARMER,
        origin=FARMER_ORIGIN,
        fidelity=Fidelity.TRANSCRIPTION,
    )
```

`fidelity` is stated here because it is a fact about acquisition. A
proofread transcription is `Fidelity.TRANSCRIPTION`. A machine-read scan is
`Fidelity.OCR`, and every record the source yields carries that value.

## Check that the source states an edition

```console
$ uv run python -c "
from saucier.infrastructure.bootstrap import farmer_source
print(farmer_source().witness.source_id)
"
```

`read_edition` raises `EditionUnstated` when the head of the file names
neither an edition nor a copyright year. That is an expected failure, not a
bug. Rename nothing to work around it. A source with no stated identity needs
a front-matter rule that reads whatever it does state.

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

`PlainText` already reads a file that carries no wrapper, which covers the
Internet Archive `_djvu.txt` form. For a third format, write a driven adapter
beside `gutenberg.py` satisfying `SourceText`: a `witness` property, a
`line_offset` property, and a `lines()` method returning body lines with the
format's packaging removed. `line_offset` is the count of file lines the
adapter stripped before the body, so a recorded line number names a line in
the file. Nothing above the adapter layer changes.

Do not loosen `GutenbergText` to accept a file with no Gutenberg markers.
That refusal is what tells you a second adapter is needed.

## For a scanned source

Wrap it in `NormalisedText`, which collapses double spacing and removes the
space before punctuation. Without it the chapter and mothers patterns fail on
whitespace alone.

```python
NormalisedText(inner=PlainText(path=..., work=..., origin=..., fidelity=Fidelity.OCR))
```

The wrapper never repairs a character. `velout^` stays `velout^`, because
repairing one witness toward another manufactures agreement between them.
See [ADR-0011](../adr/0011-normalisation-wraps-a-source.md).
