# Copilot instructions for saucier

`saucier` extracts sauce preparations from public-domain cookbooks into a
structured catalogue. It reads two witnesses of Escoffier's *A Guide to
Modern Cookery*, the 1909 revision and the 1907 first printing. It
records what each preparation is called, in which language, which mother it
derives from, and the source line the claim came from. No model runs. It backs
a blog series, and each published post corresponds to an immutable tag.

## Project stances (do not flag these as issues)

- **`parent = None` means the source stated no mother.** It never means the
  preparation has none. 74 of 124 preparations are unresolved and that number
  is correct. Do not suggest heuristics, fuzzy matching, or a model to raise
  it. A rule that resolves less and is right beats one that resolves more and
  sometimes guesses. `tests/test_corpus.py` fails if everything resolves.
  See ADR-0002.
- **Culinary terms are never translated.** Surface forms keep their diacritics
  and carry a language tag plus a concept id. Do not suggest normalising
  `Velouté` to `veloute` in stored data, or rendering `mole` as "sauce".
  Folding resolves spelling only, never meaning across languages. See ADR-0003.
- **Zero runtime dependencies is a rule.** The CLI uses `argparse` rather than
  Typer or Click, and storage uses `json` and later `sqlite3`. A reader clones
  and runs with nothing installed. Do not suggest a CLI framework. See ADR-0005.
- **`corpus/` is committed on purpose.** Two public-domain texts are tracked
  so a clone runs offline and every reader parses identical bytes. `data/` is
  ignored because it is reproducible. See ADR-0004.
- **A source states its own identity.** The `source_id` is read from the front
  matter, never taken from the filename. Do not suggest hardcoding an edition
  or deriving one from a path. See ADR-0009.
- **Fidelity is recorded, not inferred.** `corpus/escoffier-1907.txt` is OCR
  and `corpus/escoffier-1909.txt` is proofread. Do not suggest repairing the
  OCR toward the clean text, and do not suggest counting accents to guess
  fidelity. See ADR-0010.
- **A resolver may refuse, never rank.** No code path scores candidates and
  takes the best. Do not suggest a threshold, a similarity score, or a
  tie-break. See ADR-0012.
- **Four layers on a small codebase is deliberate.** `lint-imports` enforces
  domain, ports, services, adapters mechanically. Do not suggest flattening.
  See ADR-0005.
- **`...` in a `typing.Protocol` method body is idiomatic**, not an
  ineffectual statement.
- **Docstrings are heavy by policy.** Every module, class and function carries
  Google-style `Attributes:` in typed format, `Examples:` and `See Also:`.
  `docvet` and `interrogate` enforce this at 100%. It is not verbosity, and
  the cross-references render as links on the documentation site.
- **The glossary is law** (`docs/reference/glossary.md`). One term per concept:
  "preparation" never "recipe", "mother" never "base sauce", "unresolved"
  never "missing". Naming that follows it is intentional. A new term needs a
  glossary entry in the same change.
- **Prose follows a writing system** distilled from ASD-STE100. On README,
  reference pages and decision records: no semicolons, at most one em-dash per
  paragraph, sentences within 25 words, no marketing adjectives.
  `scripts/check_prose.py` enforces it. Do not suggest "more natural" phrasing
  that breaks those rules.
- **Storage is staged on purpose.** JSON now, then JSONL, SQLite, object
  storage, Postgres. Each arrives only when the previous visibly fails. Do not
  suggest jumping to a database. DuckDB was considered and rejected because it
  has no cross-process writer concurrency. See ADR-0006.
- **Tags are immutable.** A bug in a published tag gets a new patch tag, never
  a moved one.

## Worth flagging

- Anything that would make an extraction rule guess, or that treats an absence
  of evidence as evidence of absence.
- A term normalised, translated, or stripped of its language tag.
- A claim in the docs that no longer matches `uv run saucier parse` output. The
  counts 124, 50 and 74 appear in `README.md`, `docs/index.md`, and the
  tutorial. `tests/conftest.py` pins them, so a parser change fails there
  first.
- A new runtime dependency in `[project.dependencies]`.
- An import that crosses a layer boundary in the wrong direction.
- A docstring that describes behaviour the code no longer has.
- Real correctness bugs, unsafe file handling, and anything that breaks
  determinism in the parser.

## Layout

```
src/saucier/
├── domain/          frozen entities, value objects, errors. No IO.
├── ports/           Protocols. Imports domain only.
├── services/        orchestration. Imports ports and domain.
├── adapters/
│   ├── driven/      implement ports (source readers, stores)
│   └── driving/     entry points (CLI)
└── infrastructure/  config and assembly root
```

Decision records live in `docs/adr/`. Contributor rules live in
`CONTRIBUTING.md`. Agent working rules live in `CLAUDE.md`.
