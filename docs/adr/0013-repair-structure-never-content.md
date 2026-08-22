# ADR-0013: Normalisation repairs structure, never content

## Status

Accepted.

## Date

2026-08-21

## Context

ADR-0011 placed whitespace normalisation in an adapter that wraps a source,
and closed with a rule: normalisation never repairs a character. The reason
was `velout^`. Restoring it to `velouté` would manufacture agreement between
the exact two witnesses this corpus compares.

That rule drew its line in the wrong place, and a second scan artefact showed
where the line belongs.

`ENTRY` requires an em dash between an entry number and its title. The scan
does not always supply one:

```
1907:  126-- MAYONNAISE  SAUCE
1909:  126—MAYONNAISE SAUCE
```

Forty-one headings are damaged that way, eleven of them sauces. The parser
could not see them at all, so `saucier diff` reported them as sauces the 1909
revision added. Mayonnaise was never added. It was in the reader's blind spot
from the first release.

Repairing `126--` to `126—` repairs a character. Under ADR-0011 as written it
is forbidden, and the eleven sauces stay lost.

## Decision

**Normalisation may repair the punctuation that delimits a record. It may
never repair the characters that constitute one.**

Two tests separate the two, and both have to pass.

**The evidence is inside the same witness.** A line reading `126-- MAYONNAISE
SAUCE` looks exactly like the 2,622 undamaged headings in the same document:
a sequential number, a separator, an upper-case title. Nothing is borrowed
from the other witness. `velout^` fails this test. The evidence for the
missing letter is French orthography or the 1909 text, and both sit outside
the document being read.

**The repair changes no recorded byte.** The separator is consumed by the
entry pattern and never reaches a `Term`. `QRIBICHE SAUCE` is recorded as
`QRIBICHE SAUCE`, and the comparison is what notices it resembles
`GRIBICHE`. Repairing a term would change what the record says the source
said, which ADR-0003 forbids.

**A repair runs only where the line is unmistakably a record.** The guard is
narrow on purpose: a number, one or two hyphens, and a title set entirely in
upper case carrying more than three letters. The same book numbers its prose,
and `1. Ordinary and clarified consommes.` must stay a sentence.

**Declining a repair is the safe direction.** The guard rejects seven
hyphen-shaped lines in the scan. One of them is a genuine heading, `33-
CHASSEUR SAUCE (Escoffier's Method)`, held out by a lower-case parenthetical.
A twelfth sauce therefore stays invisible. Recovering it needs its own
measurement rather than a looser guard applied on the way past.

**Matching against the other witness to decide what is a record is
forbidden.** It would leak the comparand into the thing being compared. Every
difference the diff then reports would be partly an artefact of its own
matching.

## Consequences

### Positive

- Eleven sauces enter the 1907 catalogue, and the count of sauces the
  revision added falls from 20 to 10. Roughly half of that claim was the
  scanner.
- The 1907 census rises to 113 sauces, 35 derived, and 78 unresolved. The
  1909 census is untouched.
- The recovered headings carry their OCR spellings, so `QRIBICHE SAUCE` pairs
  with `GRIBICHE SAUCE` as OCR-suspected rather than standing as a difference.
- The rule is stateable in one sentence and testable in two, so a later
  repair can be argued against it rather than by taste.

### Negative

- ADR-0011's closing sentence is amended by this record. A reader following
  the older wording will find the code doing what it said it would not.
- One known sauce stays lost, and the diff still reports `CHASSEUR SAUCE` as
  an addition. That row is wrong and this release knows it is wrong.
- The wrapper now knows one thing about the document's structure: the shape
  of its own entry separator. A test asserts that a repaired line satisfies
  `extraction.ENTRY`, because nothing else couples the two.
- The guard is measured against one scan of one book. A second scanned source
  will need its own measurement, and a silent low census is how it will
  announce that.

## References

- [ADR-0003: Culinary terms carry a language tag and are never translated](0003-terms-are-never-translated.md)
- [ADR-0010: Fidelity is a property of the record](0010-fidelity-is-a-property-of-the-record.md)
- [ADR-0011: Normalisation is an adapter that wraps a source](0011-normalisation-wraps-a-source.md)
