# ADR-0003: Culinary terms carry a language tag and are never translated

## Status

Accepted.

## Date

2026-08-19

## Context

The 1907 translator of *Le Guide Culinaire* left many terms in French.
*Espagnole*, *velouté*, *béchamel* and *despumation* appear untranslated in an
English text, because each names a specific preparation rather than describing
one.

Normalising a corpus to one language is a common first step, and it is
available here. Folding *espagnole* to "brown sauce" would make lookup simpler
and the catalogue smaller.

It would also be wrong, and the cost grows as the corpus moves away from
Europe. *Mole* is Nahuatl, from *mōlli*. The vocabulary beneath it is Spanish
over a Nahuatl substrate, including *nixtamal*, *comal*, *metate* and
*epazote*. Rendering *mole* as "sauce" discards the distinction the word
exists to carry.

There is a second reason. This corpus is intended to test whether a taxonomy
induced from one tradition generalises to another. Translating everything into
English would test whether an English-shaped taxonomy fits English-translated
descriptions. That test passes for the wrong reason.

## Decision

**A term is stored as its surface form, tagged with the language it was written
in, and linked to a language-independent concept identifier. No code
substitutes a translation for a term.**

The model has three parts.

**Surface form.** The term exactly as the source writes it, including
diacritics. `Velouté` is stored as `Velouté`.

**Language tag.** An ISO 639-1 code. Inference uses three signals: diacritics,
French noun-adjective word order, and a lexicon of French terms that keep
their spelling in English.

**Concept identifier.** A folded form that resolves orthographic variation
only. `Velouté` and `VELOUTE` reach `veloute`. Folding decides nothing about
meaning, so it never resolves equivalence across languages. Establishing that
*salsa española* and *espagnole* denote one concept requires evidence.

An English rendering may be recorded beside a term as a gloss. A gloss is
labelled as one and never replaces the term.

This anticipates a translation stage. When one arrives, it may translate prose,
meaning method descriptions and commentary. It may not translate the term
layer. An unguarded translation pass renders *mole* as "sauce" and destroys the
ontology in one step.

## Consequences

### Positive

- The catalogue can represent a concept with no equivalent in any other
  language, which is the correct result for much of the mole vocabulary.
- Cross-language equivalence stays a claim requiring evidence rather than a
  side effect of string handling.
- The generalisation test stays honest, because the corpus is not pre-shaped
  toward the taxonomy being tested.

### Negative

- Lookup is harder. A reader searching for "brown sauce" must be met by the
  ending-match fallback rather than by a normalised index.
- Language inference is heuristic and will misclassify terms. The consequence
  is a wrong tag rather than lost information, because the surface form is
  preserved either way.
- Every future stage must be checked for an implicit translation step.

## References

- [Data model](../reference/data-model.md)
- [Glossary](../reference/glossary.md)
