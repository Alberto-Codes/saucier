# Contributing

This repository backs a blog series. Each published post corresponds to a tag,
and every tag runs and produces output. That shapes what changes are easy to
accept.

## Set up

```console
$ git clone https://github.com/Alberto-Codes/saucier
$ cd saucier
$ uv sync
$ uv run pre-commit install --install-hooks -t pre-commit -t pre-push
```

No GPU, no API key, no database, no network. Both source texts are committed.

## The development loop

```console
$ uv run saucier parse          # run it
$ uv run pytest -q              # fast suite
$ uv run pre-commit run --all-files
```

The last command runs every gate. If it passes, CI passes.

## What the gates enforce

They fail the build. Do not route around them.

| Gate | Holds |
| --- | --- |
| `lint-imports` | The hexagon. Domain imports nothing of ours. Services never import adapters. |
| `docvet` | Every module, class, and function documented, with typed attributes, examples, and cross-references. |
| `interrogate` | 100% docstring presence. |
| `check_doc_refs.py` | Every dotted `saucier.*` reference resolves to a real module. |
| `check_prose.py` | Strict-mode pages obey the writing system. |
| `check_banned_terms.py` | The rejected project name stays out. |
| `check_loc.py` | 300 code lines soft, 320 hard, per module. Docstrings excluded. |
| `ruff` | Sonar-adjacent rules. Complexity at most 12, arguments at most 7. |
| `pytest` | 85% coverage floor. |

## House rules

**The glossary is law.** [docs/reference/glossary.md](docs/reference/glossary.md)
holds one term per concept. It is "preparation", never "recipe". Coining a term
needs a glossary entry in the same change.

**The parser does not guess.** Prefer a rule that resolves less and is right to
one that resolves more and is sometimes wrong. The unresolved count is
published. Inflating it by guessing is the one unrecoverable mistake here.

**`None` means unresolved.** It never means "no parent". A change that treats
absence of evidence as evidence of absence will be rejected.

**Terms are tagged, never translated.** A change that normalises a term to
English is wrong however convenient it is.

## Commits and pull requests

Conventional commits. The subject is the squash commit subject, so keep it
imperative and under 50 characters.

```
feat(extraction): read mothers from the source text
fix(cli): resolve a name by its ending
docs(reference): add the glossary
```

Scopes: `domain`, `ports`, `services`, `adapters`, `cli`, `extraction`,
`corpus`, `docs`, `gates`, `ci`.

Do not put issue numbers in the scope. It breaks release-please.

Releases are cut by release-please from these commit types. A `feat` bumps the
minor version, a `fix` bumps the patch.

[Cut a release](docs/how-to/cut-a-release.md) draws the whole flow, including
the token condition that decides whether a tag reaches PyPI and Pages.

## Corpus

`corpus/` is tracked, so a clone runs with no fetch step. Only add source
material you may redistribute. United States public domain currently covers
publication through 1930. Large or restrictively licensed sources get a fetch
script and stay untracked.

A new source declares its origin and its fidelity in
`infrastructure/config.py`, and reads its own edition out of its front
matter. Never name a source from its filename.
[Add a source](docs/how-to/add-a-source.md) walks the whole path.

## Tags are immutable

A bug found in a published tag gets a new patch tag and a note. A moved tag
silently changes what a reader checked out, and a post pointing at it becomes
wrong without anyone noticing.
