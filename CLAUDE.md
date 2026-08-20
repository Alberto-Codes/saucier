# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## Project overview

**saucier** extracts structured procedures from culinary sources. This release
reads Escoffier's *A Guide to Modern Cookery* (1907) and produces a catalogue
of sauce preparations with their derivations, language-tagged and traceable to
a source line. Design rationale lives in `docs/explanation/`; the reader-facing
walkthrough is `docs/tutorial/first-run.md`.

## Rules that are enforced, not requested

These fail the build. Do not work around them.

- **`lint-imports`** — the hexagon. Domain imports nothing of ours; ports
  import domain only; services never import adapters or infrastructure.
- **`docvet`** — every module, class, and function carries a Google-style
  docstring with `Attributes:` in typed format, `Examples:`, and `See Also:`.
  Presence coverage is 100%.
- **`interrogate`** — 100% docstring presence.
- **`check_loc.py`** — 300 code lines soft, 320 hard, per module. Docstrings
  are excluded from the count, so documentation never forces a split.
- **`ruff`** — Sonar-adjacent rule set; complexity ≤ 12, arguments ≤ 7.
- **coverage** — 85% floor.

Run everything at once with `uv run pre-commit run --all-files`.

## Vocabulary

[docs/reference/glossary.md](docs/reference/glossary.md) is law: one term per
concept, one concept per term, in docs, code identifiers, commit messages, and
conversation. It is "preparation" (never "recipe"), "mother" (never "base
sauce"), "unresolved" (never "missing"). Coining a term requires a glossary
entry in the same change.

`scripts/check_doc_refs.py` verifies that every dotted `saucier.*` reference
in docs and docstrings resolves to a real module or attribute. Refactors move
modules; prose does not notice.

## Writing system

Distilled from ASD-STE100. Two modes.

**Strict mode** — ADRs, reference pages, README, error messages, CLI help,
commit messages, code comments. A misread here costs cycles:

1. One instruction per sentence, at most 20 words. Descriptive sentences at
   most 25.
2. Active voice; name the actor ("the parser rejects...", not "it is
   rejected").
3. Verbs for actions, not nouns: "extract", never "perform an extraction".
4. No hedging stacks. State the fact or write an explicit **Open question**.
   "May potentially help improve" is banned.
5. No marketing adjectives: seamless, robust, powerful, blazing. Show the
   number instead.
6. No semicolons. At most one em-dash per paragraph.
7. Single verbs over phrasal verbs: "remove", not "take off".
8. State numbers and units: "102 unresolved", not "many".

**Flavored mode** — explanation pages, discussions, PR descriptions. Keep the
glossary discipline, active voice, and one-idea-per-sentence habit. Range,
analogy, and voice are allowed. Explanation pages are where thinking happens,
so do not strangle them.

Style rules govern *form*. They do not make a claim true.

## Principles this codebase holds

**`None` means unresolved, never "none".** A preparation whose source states
no base has `parent = None`. That is an absence of evidence, and no code may
treat it as evidence of absence.

**Terms are tagged, never translated.** `mole` is not "sauce". Surface forms
are preserved with a language tag and a concept id. Any change that
normalises a term to English is wrong regardless of how convenient it is.

**Every claim carries provenance.** A `SourceRef` with an entry and a line
number, checkable by hand against `corpus/`.

**The parser does not guess.** When adding extraction rules, prefer a rule
that resolves less and is right to one that resolves more and is sometimes
wrong. The unresolved count is a published number; inflating it by guessing
is the one unrecoverable mistake here.

## Layout

```
src/saucier/
├── domain/          # frozen entities, value objects, errors. No IO.
├── ports/           # Protocols. Imports domain only.
├── services/        # orchestration. Imports ports + domain.
├── adapters/
│   ├── driven/      # implement ports (source readers, stores)
│   └── driving/     # entry points (CLI)
└── infrastructure/  # config and assembly root
```

## Corpus and data

- `corpus/` is **tracked**. Small, public-domain source material, so a clone
  runs with no fetch step and every reader gets identical bytes.
- `data/` is **not tracked**. Everything in it is reproducible by
  `uv run saucier parse`.
- Do not commit anything to `corpus/` that cannot be redistributed. Large or
  restrictively licensed sources get a fetch script instead.

## Working here

- Branch. Do not commit to `main`.
- No `Co-Authored-By` or session trailers in commit messages.
- Tags are immutable. A bug found in a published tag gets a new patch tag plus
  a note, never a moved tag.
