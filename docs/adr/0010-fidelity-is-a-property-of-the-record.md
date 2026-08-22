# ADR-0010: Fidelity is a property of the record, not a caveat in a paragraph

## Status

Accepted.

## Date

2026-08-21

## Context

The corpus now holds two witnesses of one work. Gutenberg 71395 is a
transcription proofread by the Distributed Proofreaders. Internet Archive
`cu31924000610117` is raw OCR of a Cornell University Library scan.

The two are not equal evidence. In the OCR witness every accent is destroyed.
`velouté` reads `velout^`. `purée` reads `pur^e`. A systematic `g` to `q`
substitution turns `ravigote` into `raviqote` and `genevoise` into
`qenevoise`.

Identity survives that damage, because `to_concept_id` already folds
diacritics. The surface form does not survive it.

ADR-0003 says a term is stored as its surface form and is never altered. For
an OCR witness the preserved surface is `VELOUTE`, and recording that as what
the source said is false. The book says `VELOUTÉ`. The scan says `VELOUTE`.

**What the artifact says is not what the work says.** A transcript is
evidence of an original rather than the original.

There is a second cost, and it is the one that reaches the diff. Every
difference between the two witnesses now has two explanations. It is a
revision, or it is a scan artifact. A schema that cannot say which text a
claim came through has thrown away the only information that separates them.

## Decision

**Every record states how its text was obtained.**

**`Fidelity` has two values.** `transcription` is proofread by hand.
`ocr` is machine-read from a scan. Adding a value means adding a witness that
was obtained a third way.

**Fidelity is stated, never inferred.** It is a fact about acquisition rather
than about the text, so it is recorded beside the URL the text came from. No
code guesses fidelity by counting accents.

**`SourceRef` carries it.** One preparation lifted out of a catalogue file
still says which text its line number points into. A citation that cannot be
graded is a citation a reader has to grade twice.

**`Catalogue` carries a `Witness`.** The witness holds the work, the edition
read from the front matter, the fidelity, and the origin the text was fetched
from. A stored catalogue therefore states what it is without a reader
consulting the repository.

**A catalogue refuses to hold a record that disagrees with its witness.**
Two places record fidelity, so the entity rejects the state where they
contradict each other.

**Surface forms are still preserved exactly, and ADR-0003 is unchanged.** The
surface recorded is the surface the witness carries. Fidelity is what tells a
reader whether that surface is the work or a reading of it.

## Consequences

### Positive

- A cross-edition difference can be attributed. `saucier diff` marks a row
  OCR-suspected because it knows one witness is OCR.
- The OCR witness enters the corpus without a caveat paragraph that a reader
  has to remember while reading a table.
- Repairing the OCR toward the clean text stays out of scope. The reason is
  visible in the record rather than argued in prose.
- The 1907 first printing parses to 102 sauces, 32 derived, and 70
  unresolved. Those numbers are usable because their fidelity is stated.

### Negative

- `SourceRef` gains a fourth field, and every construction site states it.
- Fidelity is recorded twice, on the catalogue and on each reference. The
  entity check costs one pass per catalogue construction.
- Two values are too few for the real world. A witness that is OCR plus a
  partial hand correction has no honest value here. Adding one means
  revisiting every comparison that reads the field.
- Nothing enforces that the declared fidelity is true. A mislabelled witness
  produces confident wrong attribution, which is the failure mode this record
  exists to name.

## References

- [ADR-0003: Culinary terms carry a language tag and are never translated](0003-terms-are-never-translated.md)
- [ADR-0009: The source states its own identity](0009-the-source-states-its-own-identity.md)
- [ADR-0011: Normalisation is an adapter that wraps a source](0011-normalisation-wraps-a-source.md)
- [Glossary](../reference/glossary.md)
