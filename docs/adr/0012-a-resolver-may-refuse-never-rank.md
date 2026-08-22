# ADR-0012: A resolver may refuse, never rank

## Status

Accepted.

## Date

2026-08-21

## Context

`AURORE SAUCE` reads the same in both printings, word for word:

> Into one-half pint of boiling velouté put the same quantity of very red
> tomato purée (No. 29), and mix the two.

Two candidates are stated. The resolver refuses to choose between them and
records unresolved, which ADR-0007 requires.

In the OCR witness `velouté` reads `velout^`. One candidate becomes
invisible. The resolver now sees one unambiguous candidate and records
`tomato`.

The OCR did not add noise to that record. It removed the ambiguity that was
the reason for the honest answer. The result is well-formed, provenanced to a
real line, and wrong. ADR-0001 named this failure mode before it was
observed. A rigorous schema over noisy extraction produces well-formed wrong
answers, and those are worse than obviously wrong ones because they validate.

The error was caught by one mechanism only. The clean witness refused and the
OCR witness answered, and the discontinuity between them was visible.

A similarity score over both witnesses returns a confident parent for both.
The refusal never happens, the discontinuity never appears, and the finding
becomes undetectable. That change would read as pure progress. Resolving 74
more preparations is the sentence a release note wants to carry.

A model layer is coming, and it will arrive with a threshold.

## Decision

**A resolver returns a parent or refuses. It never returns a ranking.**

**No code path scores candidates and takes the best.** Two stated candidates
resolve to `None`, whatever the relative strength of the two statements.

**A proposal from a model is a witness, not a value.** When a model layer
arrives it may record a proposed parent with the proposer named beside it. It
may not write that proposal into `parent`, and it may not clear an
abstention.

**Abstention is an instrument rather than a gap in coverage.** The unresolved
count is published for that reason. A release that lowers it must say which
rule read which text, and the reading must be checkable by hand.

## Consequences

### Positive

- The one signal that catches silent corruption survives contact with a
  model.
- `saucier diff` can report a parent disagreement without adjudicating it,
  because neither side ever claimed a confidence.
- The rule is stated before the code it governs, which is the point of the
  practice.

### Negative

- 74 of 124 preparations stay unresolved, and the number will not fall for
  any cheap reason.
- A model that could resolve a genuine derivation still cannot write it into
  `parent`. Recording the proposal beside the field costs a schema change
  that this release does not make.
- The rule is easy to break by accident. Any `sorted(candidates)[0]` is a
  ranking wearing the costume of determinism, and no gate detects one.

## References

- [ADR-0002: An unresolved parent is recorded as absent, never inferred](0002-unresolved-is-not-none.md)
- [ADR-0007: The source decides what counts as a sauce](0007-the-source-classifies-its-own-contents.md)
- [ADR-0010: Fidelity is a property of the record](0010-fidelity-is-a-property-of-the-record.md)
