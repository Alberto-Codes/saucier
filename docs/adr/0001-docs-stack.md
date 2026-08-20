# ADR-0001: The documentation stack, and why it is pinned on both sides

## Status

Accepted.

## Date

2026-08-19

## Context

The docstrings in this repository carry mkdocstrings cross-reference syntax,
for example `[saucier.domain][]`. `check_doc_refs.py` proves those paths
resolve to real modules. Only a site renders them as links, so a documentation
site is not decoration here. It is what makes 74 existing references work.

The MkDocs ecosystem split during 2026.

- [`mkdocs`](https://pypi.org/project/mkdocs/) last released 1.6.1 on
  2024-08-30. Its maintainer announced a version 2 that supports no existing
  theme, plugin, or configuration file.
- [`mkdocs-material`](https://pypi.org/project/mkdocs-material/) remains
  actively maintained and caps `mkdocs<2` from version 9.7.5, so an accidental
  upgrade cannot break a build.
- [`properdocs`](https://pypi.org/project/properdocs/) is a community
  continuation of MkDocs 1.x and a drop-in replacement. It is at 1.6.7,
  released on 2026-03-20.
- [`mkdocs-materialx`](https://pypi.org/project/mkdocs-materialx/) is a
  community continuation of Material, forked at 9.7.1. It is at 10.2.0,
  released on 2026-07-23.
- [`zensical`](https://pypi.org/project/zensical/) comes from the Material team
  and is positioned as the long-term replacement. It is at 0.0.56, released on
  2026-08-18.

Each entry links to the package index rather than to a homepage. A reader
revisiting this record needs the current release state, which is what that page
shows.

## Decision

**Stay on `mkdocs` 1.x with `mkdocs-material`, and pin an upper bound on every
documentation dependency.**

The mkdocstrings chain this project depends on — `mkdocs-gen-files`,
`mkdocs-literate-nav`, `mkdocs-section-index` — targets MkDocs 1.x. Moving off
it means moving all of them at once, for no benefit the site needs today.

Upper bounds are set on every entry rather than on `mkdocs` alone. A caret-free
floor on a package whose ecosystem is mid-split invites a surprise major
release to break a build that nobody was watching.

`griffe` carries no bound in this extra. `mkdocstrings-python` 2.x depends on
[`griffelib`](https://pypi.org/project/griffelib/), not on `griffe`, so a cap
copied from an older project is both stale and wrong. It caused an
unsatisfiable resolution when first written.

**Zensical is the thing to watch.** It comes from the team that maintains the
theme this site uses, and it is a declared drop-in replacement. Revisit when
it reaches a stable major version. Do not adopt a 0.0.x release for
documentation that ships as part of the deliverable.

## Consequences

### Positive

- The site builds today, `--strict`, with no warnings that affect output.
- The 74 dotted references in docstrings render as links.
- The API reference is generated from docstrings, so it cannot drift from the
  code.
- Every bound is explicit, so a breaking release fails resolution rather than
  the build.

### Negative

- The stack rests on an unmaintained core. That is a known, dated risk rather
  than a discovered one.
- A future move to Zensical or ProperDocs will move several packages at once.
- Upper bounds need review when a dependency ships a major version, which is
  work dependabot will surface but not decide.
