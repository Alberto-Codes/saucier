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

**JSON is going to stop being enough.** Appending one record will mean
rewriting the file, and the store becomes SQLite, then Postgres. Because
services depend on `CatalogueStore` and not on `JsonCatalogueStore`, that is a
new module beside the old one plus one line in the assembly root. No service
changes. No test of the extraction logic changes.

**Video is going to arrive.** It satisfies the same `SourceText` contract as a
text file: something with an id that yields lines. The extraction service does
not learn that video exists.

**Extraction is going to get a model.** It is a service, so it can be replaced
or supplemented without any adapter knowing.

## What it costs

Seven `__init__.py` files, two protocol modules that hold no logic, and an
assembly root. That is the whole overhead, and `check_loc.py` keeps any single
module under 320 code lines so the structure stays legible rather than
becoming the point.

The failure mode this avoids is the common one: a parser that reads files
directly, then gets a database bolted on, then a model, until the extraction
rules and the IO cannot be separated and neither can be tested alone.
