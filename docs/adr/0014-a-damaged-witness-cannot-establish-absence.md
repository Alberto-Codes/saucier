# ADR-0014: A damaged witness cannot establish absence

## Status

Accepted.

## Date

2026-08-22

## Context

`saucier diff` reported eight sauces the 1909 revision added. All eight are in
the 1907 printing, at the same entry number, under the same heading.

```
1907:  6s— BERCY  SAUCE          1909:  65—BERCY SAUCE
1907:  loi— POULETTE  SAUCE      1909:  101—POULETTE SAUCE
1907:  I22~ANDAL0USE  SAUCE      1909:  122—ANDALOUSE SAUCE
```

The scanner corrupted the marker rather than the heading. A digit read as a
letter, a space inside a number, a tilde for an em dash. The parser never saw
the entry, so the comparison saw a concept in one witness and not the other,
and called it an addition.

Two earlier releases mended two shapes of the same damage. These are four
more, and mending them would leave a fifth shape unmended and the same claim
resting on it.

The measurement that settles it: the parser reads **2,679** entries in the
scan against **2,963** in the transcription. That is a **284-entry blind
spot**. "Not in the 1907 printing" and "not found in the 1907 printing"
differ by exactly those 284 entries. The diff has been saying the first while
knowing only the second.

## Decision

**Absence is only observable through an instrument that can see everything
present. Where the instrument has a measured blind spot, absence is
unobservable and is not reported as observed.**

**A comparison involving an OCR witness reports `unmatched`.** The cause says
the diff found no counterpart. It says nothing about what either book
contains. The row still names the witness that holds the concept, so a reader
loses no information, only a claim that was never established.

**`added` and `removed` survive between two witnesses of equal fidelity.**
The rule is about damage, not about comparison. Two proofread texts are an
instrument with no measured blind spot, and absence is observable through
them.

**The blind spot is printed with the counts.** Entries read from each
witness, and the gap between them, sit in the summary rather than in a note.
No reader sees how many rows the diff found without also seeing how much of
the source it could not read.

**The blind spot is what has to shrink before the claim returns.** Restoring
`added` for a scanned witness is not a matter of taste or of a better
comparison. It requires reading the entries the parser currently cannot see,
and measuring what is left.

This is ADR-0002 and ADR-0012 applied to a third surface. An unresolved
parent is recorded as absent rather than inferred. A resolver refuses rather
than ranks. An absent preparation is now recorded as not found rather than as
absent. One rule, three places.

## Consequences

### Positive

- The release states nothing about Escoffier that its evidence cannot carry.
  No editorial difference between the two printings is confirmed, and that is
  the finding.
- A reader sees the instrument's limit beside its output, which is the
  ordinary standard for a measurement and was missing here.
- Closing the blind spot now has a number attached to it, so the work has a
  before and an after rather than a feeling.
- The eight false additions cannot come back by a route that looks like a
  feature, because restoring the cause requires the measurement.

### Negative

- The diff says less. Eight rows that read as findings now read as questions,
  and a reader who wanted a number is given a smaller one.
- `unmatched` is weaker language, and weaker language is easy to argue away.
  A future contributor will read it as timidity rather than as a rule.
- The rule is coarse. A witness with a one-entry blind spot is treated like a
  witness with 284, because the alternative is a threshold nobody can defend.
- The blind spot is measured against the other witness, so a work with only
  one scanned witness has no way to state its own.

## References

- [ADR-0002: An unresolved parent is recorded as absent, never inferred](0002-unresolved-is-not-none.md)
- [ADR-0010: Fidelity is a property of the record](0010-fidelity-is-a-property-of-the-record.md)
- [ADR-0012: A resolver may refuse, never rank](0012-a-resolver-may-refuse-never-rank.md)
- [ADR-0013: Normalisation repairs structure, never content](0013-repair-structure-never-content.md)
