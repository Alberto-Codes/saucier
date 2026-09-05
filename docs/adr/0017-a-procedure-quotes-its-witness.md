# ADR-0017: A procedure quotes its witness

## Status

Accepted.

## Date

2026-09-04

## Context

A preparation records one parent and nothing about what is done with it.
`MORNAY SAUCE` is entry 91, at line 2437 of the 1909 text. Its `parent` is
`bechamel`. The catalogue says Mornay derives from Béchamel and does not
say how.

The body says how. It boils one pint of Béchamel with one-quarter pint of
fumet. It reduces by a good quarter. It adds two oz. each of Gruyère and
grated Parmesan. It returns the sauce to the fire for a few minutes and
stirs with a small whisk until the cheese melts. It finishes away from the
fire with two oz. of butter, added by degrees. That is six operations, five
inputs with quantities, two criteria, three constraints, one instrument,
and one duration. Every one of them is a run of words a reader can point
at, and none of them is inferred.

ADR-0015 left ten sauces unresolved because a second catalogued name sits
in their opening paragraph. `CARDINAL SAUCE` boils Béchamel and finishes
with lobster butter. The names are two candidates. The verbs are one base
and one finish. ADR-0015 says that reading the verb a name sits in is a
later record. This is that record, and it stops short of resolution.

The parent edge is an input with its operation stripped off. The
destination of the series needs the operation. "Reduce by a good quarter"
and "grind on the metate until smooth" have one shape. Each is an
operation with an optional instrument and a stated criterion. Each carries
parameters the text either numbers or does not.

## Decision

**A preparation may carry a procedure. A procedure is the operations the
body states, in the order it states them, in the witness's own words.**

**Every element quotes its witness.** An operation carries its `wording`,
which is the clause it was read from. Each input, criterion, duration, and
constraint carries its own wording, and that wording lies inside the
operation's. The entity refuses an element whose words are not inside its
operation. A procedure reports every operation whose words the body does
not carry in that order. A procedure can therefore say nothing the text
does not say.

**A number the text does not give is unresolved.** A parameter holds the
words, the number they give, and the unit they name. `one-quarter pint`
records `1/4` and `pint`. `a few minutes` records `minutes` and no number.
`by a good quarter` names a degree and not a number, so its number is
unresolved too. No code fills a number the words do not carry. ADR-0002
governs the slot.

**Verbs and instruments are terms.** `Boil` is an English term with the
concept `boil`. A source in another language states its operations in that
language, and ADR-0003 forbids translating them.

**One preparation, recorded by hand, once per witness.** This release
records Mornay and nothing else. Each witness gets its own procedure, in
the words that witness carries. A recorded procedure enters through a
port, `RecordedProcedures`, and the only implementation holds two written
by hand. A rule reader or a model reader is another implementation behind
the same port, and it names itself. A test pins the count at one recorded
preparation per witness. A change that records a second one adds its hand
check in the same change, or fails.

**The parent is untouched.** The procedure sits beside `parent` and never
writes it. Mornay's first operation boils Béchamel, which is its parent.
The derivation now carries its verb. Cardinal's ten stay unresolved,
because no rule reads a verb yet. Reading them by rule is the record after
this one.

**The procedure is not stored, and the interchange does not carry it.**
`saucier show` fetches it beside the preparation, checks it against the
body, and prints it. `data/` is unchanged, and `saucier/1` is unchanged.
ADR-0016 says a new field needs a new schema version, and one recorded
preparation does not earn one.

### Three decisions the reader made

The words leave three things open. The reader chose each one, and each
choice is checkable against the clause it was made in.

The verb of an operation is the action the cook performs. `ensure the
melting of the cheese by stirring with a small whisk` records `stirring`.
`the melting of the cheese` is its criterion, and `small whisk` is its
instrument.

`the sauce` and `the cheese` name the preparation in progress. They are
not inputs.

`Put the sauce on the fire again` records `Put`, with `on the fire again`
as its constraint. The text names no heat, so no heat is recorded.

### What the scan says

The 1907 witness carries Mornay at line 2864, and its procedure quotes the
scan as the scan reads.

- The heading reads `MORN AY SAUCE`. The concept is `morn-ay-sauce`, so
  `saucier show mornay` finds nothing in the scan.
- The first input reads `Bdchamel Sauce`. Its concept reaches no catalogued
  name, so the scan's Mornay is unresolved with no candidate. The proofread
  text resolves it. The verb is on the record in both.
- `Gruyère` reads `Gruy^re`.
- The reduce operation crosses a page break. Its wording carries the
  running header `40 GUIDE TO MODERN COOKERY`, because the scan carries it
  there. Removing it is normalisation. ADR-0011 puts that in the adapter,
  and ADR-0013 limits it to structure. This record does neither.
- The fumet is `of that fish which is to constitute the dish` in 1907 and
  `of the fish, poultry, or vegetable, which is to constitute the dish` in
  1909. No scanner adds two nouns and a comma. That is an editorial
  difference between the two printings, and it is the first this project
  has confirmed. It was confirmed by hand, on two lines a reader can open.

## Consequences

### Positive

- The shape exists and one preparation fills it. A reader can print it and
  check every word against `corpus/`.
- Mornay's derivation has a verb, a quantity on each side, and a criterion
  for the reduction.
- The unresolved slot is used for the first time on something other than
  a parent. `a few minutes` is a stated duration with no number.
- The census does not move. 151, 57, and 94 stand, and so do 140, 50, and
  90.
- The first editorial difference between the printings is on the record,
  with both readings quoted.

### Negative

- Two procedures by hand is not extraction. The count of recorded
  preparations stays at one until a rule reads a second.
- The two procedures are Python literals in an adapter. A file under a
  tracked directory is a later store, and ADR-0006 governs when it arrives.
- A wording quotes markup and page furniture where the witness carries
  them. `_fumet_` keeps the underscores of the transcription, and the
  scan's reduce keeps a running header.
- The check is a substring test on collapsed whitespace. It proves the
  words are there and in order. It does not prove the reader parsed the
  clause.
- The interchange cannot carry a procedure, so a consumer of the stream
  does not see it.
- Three choices are the reader's, and a second reader may make them
  differently. They are stated above so that a disagreement is visible.

## References

- [ADR-0002: An unresolved parent is recorded as absent, never inferred](0002-unresolved-is-not-none.md)
- [ADR-0003: Culinary terms carry a language tag and are never translated](0003-terms-are-never-translated.md)
- [ADR-0012: A resolver may refuse, never rank](0012-a-resolver-may-refuse-never-rank.md)
- [ADR-0013: Normalisation repairs structure, never content](0013-repair-structure-never-content.md)
- [ADR-0015: The chapter decides](0015-the-chapter-decides.md)
- [ADR-0016: JSONL is the interchange, not a store](0016-jsonl-is-the-interchange-not-a-store.md)
- [Glossary](../reference/glossary.md)
