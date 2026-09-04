# Why the layers, on a project this small

A parser and a CLI do not need four layers. This one has them because of what
arrives next, and because the boundaries are cheaper to install now than to
retrofit.

## The rule

```
domain      imports nothing of ours
ports       imports domain only
services    imports ports and domain, never adapters
adapters    implement ports; nobody imports them but the assembly root
```

This is checked by `lint-imports` on every commit, not trusted to discipline.
A service that imports an adapter fails the build.

## What it buys, concretely

**JSON is going to stop being enough.** Not the way the first draft of this
page predicted. It said appending one record would mean rewriting the file.
The store writes one file per witness, so that never happened. What did
happen is that nothing outside this process could read a catalogue without
learning the nested document first. So the second port arrived before the
second store: `CatalogueInterchange`, with a JSON Lines adapter behind it.
[ADR-0016](../adr/0016-jsonl-is-the-interchange-not-a-store.md) records why
a serialization is not a database. When SQLite does arrive, it is still a new
module beside `JsonCatalogueStore` plus one line in the assembly root,
because services depend on `CatalogueStore` and not on the JSON. No service
changes. No test of the extraction logic changes.

**Video is going to arrive.** It satisfies the same `SourceText` contract as a
text file: something that reports the witness it is and yields lines. The
extraction service does not learn that video exists.

**Extraction is going to get a model.** It is a service, so it can be replaced
or supplemented without any adapter knowing.

## What it has already bought

The source port had exactly one implementation from v0.1.0 to v0.2.0, which
means it was never tested as a boundary. A port with one adapter behind it is
a guess about where the seam goes.

The 1907 witness paid the first rent. It is an Internet Archive `_djvu.txt`
with no Gutenberg markers, and `GutenbergText` refuses it — correctly, because
a reader that stretches to fit a second format has stopped checking the first.
So `PlainText` reads it, and nothing above the adapter layer changed.

Then the scan needed its whitespace cleaned before the extraction patterns
matched, and the three lines that do it had three bad homes: inside a source,
where every future source rewrites them; inside the service, where the domain
learns what OCR is; or in a fifth layer built to hold three lines.
`NormalisedText` is the fourth answer. It implements the port *and* consumes
it, so it wraps any source, lives in the adapter layer, and adds no layer at
all. `lint-imports` needed no new contract for it.

That is the boundary doing the work it was installed for, on the first
occasion it was asked. [ADR-0011](../adr/0011-normalisation-wraps-a-source.md)
records the argument.

## What it costs

Eight `__init__.py` files, two protocol modules that hold no logic, and an
assembly root. That is the whole overhead, and `check_loc.py` keeps any single
module under 320 code lines so the structure stays legible rather than
becoming the point.

The failure mode this avoids is the common one: a parser that reads files
directly, then gets a database bolted on, then a model, until the extraction
rules and the IO cannot be separated and neither can be tested alone.
