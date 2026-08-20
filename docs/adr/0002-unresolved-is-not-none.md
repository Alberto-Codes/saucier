# ADR-0002: An unresolved parent is recorded as absent, never inferred

## Status

Accepted.

## Date

2026-08-19

## Context

The parser reads 166 sauce preparations from Escoffier. It links 64 of them to
a mother. The remaining 102 name no mother in their opening paragraph, so their
`parent` field is `None`.

That number is the project's headline claim. It appears on the landing page, in
the tutorial, in the README, and in the argument for why a model comes later.

`None` is an ambiguous value. It can mean "this preparation has no mother" or
"the source did not say". Only the second is true here. Escoffier wrote for a
reader who already knew that a Bordelaise finishes with an Espagnole, so he did
not write it down. The knowledge exists. The sentence does not.

A contributor improving parser coverage will reach for a heuristic. Mentioning
a mother anywhere in the prose, matching an ingredient list, or asking a model
would each raise the resolved count. Each would also convert 102 honest
absences into confident assertions, most of them unverifiable against the text.

The failure is silent. Coverage improves, the tests still pass, and the
project's central number becomes a claim about the parser rather than about the
source.

## Decision

**`parent = None` means the source stated no mother. It never means the
preparation has none, and no code may treat the two as equivalent.**

Three rules follow.

**A derivation is recorded only from a plain statement.** The mother must
appear in the entry's opening paragraph, which is where Escoffier states what a
preparation is built from. A mother named eight paragraphs later is usually
being compared against, not built on.

**A rule that resolves less and is right beats a rule that resolves more and is
sometimes wrong.** When a proposed extraction rule would raise the resolved
count, the question is not how many it adds. The question is how many of the
additions can be checked against a line in `corpus/`.

**The unresolved count is published and is not a target.** It appears in the
`parse` output, in the docs, and in the test suite. `tests/test_corpus.py`
asserts that it stays above zero, so a change that resolves everything fails
rather than passes.

A later stage may fill these in. A model that recovers knowledge an author
assumed is the entire argument for adding one. That stage must record what
filled the value and from what evidence, so an inference is never
indistinguishable from a reading.

## Consequences

### Positive

- The headline number describes the source, not the parser. It stays true when
  the parser changes.
- The gap is legible, so the case for a model is made from measurement rather
  than assertion.
- A contributor who raises coverage by guessing fails a test rather than
  shipping.

### Negative

- The resolved count looks poor next to a system willing to guess. Anyone
  comparing on coverage alone will find this project worse.
- The rule needs restating in review. Raising coverage is a natural thing to
  attempt, and the reasoning against it is not visible in the code.
- Downstream consumers must handle a null parent rather than assume a tree.

## References

- [Why there is no model in this yet](../explanation/why-no-model-yet.md)
- [Data model](../reference/data-model.md)
- [Glossary](../reference/glossary.md)
