# ADR-0007: The source decides what counts as a sauce

## Status

Accepted.

## Date

2026-08-19

## Context

The first extraction rule admitted an entry when its heading said "sauce", or
when the folded heading contained a mother concept anywhere inside it. The
second half of that rule was a substring test. Two of the five mothers
Escoffier names are ordinary English words in a cookery book.

The result was a catalogue of 166 preparations. Reading the 46 admitted by the
mother test showed roughly 40 that are not sauces:

- 25 velouté **soups**, from the soup chapter.
- 8 tomato dishes and preserves, including `TOMATO JAM` and `TOMATO SALAD`.
- 6 fish and meat dishes, including `SOLE A LA HOLLANDAISE`.
- `BOMBE HOLLANDAISE`, which is vanilla ice cream in a mould.

`GRILLED TOMATOES` was recorded as deriving from the mother sauce Tomato,
because the word "tomatoes" appears in its prose. That is an absence of
evidence turned into a derivation, published with a line number.

The damage reached the published census. 30 of the 64 recorded derivations
belonged to entries that are not sauces. The number the project asks to be
judged on described the parser rather than the source.

A dish filter rejected any heading containing "with" or the plural "sauces".
It ran before the acceptance test, so it also dropped `SOUBISE SAUCE WITH
RICE` and two other real sauces.

## Decision

**An entry enters the catalogue only on evidence the source itself supplies,
and the source supplies two kinds.**

**The heading says so.** A heading qualifies when it uses the singular word
"sauce" before any "with". `SOUBISE SAUCE WITH RICE` is a sauce served with
something. `ASPARAGUS WITH VARIOUS SAUCES` is something served with a sauce. A
heading that names its sauce after a comma names an accompaniment, so
`MAQUEREAU BOUILLI, SAUCE AUX GROSEILLES` is a dish.

**The chapter says so.** Escoffier titles three chapters `THE LEADING WARM
SAUCES`, `THE SMALL COMPOUND SAUCES`, and `COLD SAUCES AND COMPOUND BUTTERS`.
An entry whose heading names a mother but never says "sauce" qualifies only
inside one of those chapters. This keeps `LENTEN ESPAGNOLE`, and it keeps the
soup chapter out.

Reading the chapter titles is the same move as reading the mothers out of the
text. Deciding for ourselves that a velouté soup is not a sauce would not be.

**A mother must match a whole word.** Concept ids are compared word by word,
so `tomatoes` is not `tomato`.

**An ambiguous base resolves to nothing.** When an opening paragraph names two
mothers, the parser records `None`. `SHRIMP SAUCE` says "fish velouté or,
failing this, Béchamel". The source named both and chose neither. The previous
rule sorted the candidates and took the first alphabetically. That is an
arbitrary choice wearing the costume of determinism, and it was wrong in all
three entries it decided.

## Consequences

### Positive

- The census fell from 166 to 124, and derivations from 64 to 29. Both numbers
  now describe sauces. The unresolved count fell from 102 to 95 for the same
  reason: 40 of the entries counted before were never sauces.
- Every recorded parent is a mother the source named, in the prose of an entry
  the source filed as a sauce.
- Three real sauces that the dish filter dropped are back.
- The rule is checkable. A reader can open the chapter and see the title.

### Negative

- The catalogue is smaller, and a reader comparing on size alone will find
  this release worse than the last description of it.
- The chapter test binds the extractor a little more tightly to a source that
  divides itself into titled chapters. A source without them falls back to the
  heading test alone, and will resolve less.
- Sweet sauces in the entremets chapter enter on their headings only. A sweet
  sauce whose heading omits the word is missed.

## References

- [ADR-0002: An unresolved parent is recorded as absent, never inferred](0002-unresolved-is-not-none.md)
- [Data model](../reference/data-model.md)
- [Glossary](../reference/glossary.md)
