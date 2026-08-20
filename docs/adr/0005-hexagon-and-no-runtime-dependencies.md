# ADR-0005: Four layers and no runtime dependencies

## Status

Accepted.

## Date

2026-08-19

## Context

The implementation is roughly 900 lines. It reads one text file and writes one
JSON file. Four architectural layers and a zero-dependency rule are more
structure than that needs today.

Both choices are made against what arrives next rather than against what exists
now. The roadmap adds a second storage backend, then video sources, then a
model in the extraction step. Each of those replaces one component and should
touch nothing else.

The dependency question is separate and narrower. A CLI framework such as Typer
would produce a better interface than `argparse` with less code. It would also
mean that the first command in the tutorial installs something.

## Decision

**Keep the hexagonal layout, and enforce it mechanically rather than by
convention.**

```
domain      imports nothing of ours
ports       imports domain only
services    imports ports and domain, never adapters
adapters    implement ports, and only the assembly root imports them
```

`lint-imports` checks these on every commit. A service that imports an adapter
fails the build rather than passing review.

The layers earn their place at three known points. Storage moves from JSON to
SQLite to Postgres. Services depend on `CatalogueStore`, not on
`JsonCatalogueStore`. That change is a new module plus one line in the assembly
root. Video satisfies the same `SourceText` contract as a text file, so the
extraction service never learns that video exists. Extraction is a service, so
a model can replace it without any adapter knowing.

`scripts/check_loc.py` caps a module at 300 code lines soft and 320 hard, with
docstrings excluded from the count. The structure stays legible rather than
becoming the subject.

**Ship no runtime dependencies.** The command line interface uses `argparse`
from the standard library. Storage uses `json`, and `sqlite3` when that
arrives. A reader clones the repository and runs it. Nothing is installed, no
version resolves, and no dependency can break a tag that was working.

This constrains only the runtime. Development dependencies are unconstrained,
and the gates use many.

## Consequences

### Positive

- Each planned change touches one layer, which is the whole reason for the
  structure.
- The import rules are enforced, so they hold under contributors who have not
  read this record.
- A published tag keeps working, because no runtime resolution can change under
  it.
- The tutorial has no install step beyond `uv sync` for the development tools.

### Negative

- Seven package files, two protocol modules holding no logic, and an assembly
  root, for 900 lines of behaviour. A reader arriving cold sees ceremony.
- `argparse` is more verbose than a modern CLI framework, and its help output is
  plainer.
- The zero-dependency rule will be tested. Video decoding and embeddings cannot
  be done from the standard library, and this record does not decide that case.
  It decides that adding the first runtime dependency is a decision, not a
  convenience.

## References

- [Why the layers, on a project this small](../explanation/hexagon.md)
- [ADR-0006: Storage arrives in stages](0006-storage-arrives-in-stages.md)
