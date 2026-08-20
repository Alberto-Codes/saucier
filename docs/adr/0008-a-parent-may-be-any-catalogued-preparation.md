# ADR-0008: A parent may be any catalogued preparation

## Status

Accepted.

## Date

2026-08-20

## Context

The first parent rule resolved only the five mothers. An opening paragraph
naming exactly one mother recorded a derivation, and everything else recorded
`None`. That rule read 29 derivations out of 124 preparations.

The source states more than the rule could read. `MARROW SAUCE` (entry 45,
line 1895) says "the Marrow Sauce being only a variety of the Bordelaise",
with a cross-reference number. The record still said `parent: None`, because
Bordelaise is not a mother. Escoffier's structure is not a five-way star. It
is a graph with depth, and the old rule flattened it.

Widening the candidate set widens the ways a match can be wrong. Three
appeared while building this rule:

- `HORSE-RADISH SAUCE` (entry 138) opens with "finely-rasped horse-radish".
  The words match a name of entry 119, `HORSE-RADISH OR ALBERT SAUCE`. The
  entry states an ingredient, not a parent.
- `GENEVOISE SAUCE` (entry 38) opens with "add one pint of Lenten
  Espagnole". The word "Espagnole" sits inside that name. Reading both names
  turns one statement into a false ambiguity.
- Folding an opening flattens punctuation, so a matcher can join words
  across a full stop. That is the substring defect of ADR-0007 in a new
  disguise.

## Decision

**A stated parent may be any catalogued preparation, not only a mother. What
counts as a statement is narrowed to keep every recorded link checkable.**

**The candidates are the catalogue's own names.** Every term of every kept
preparation, every folded title, and every declared mother is a candidate.
Nothing else is. Two names that reach one preparation count as one candidate.

**A statement is a whole run of words inside one sentence.** The run must sit
in the opening paragraph, as before. `tomatoes` is not `tomato`, and a name
split across a full stop is not a statement.

**A run inside the entry's own name is not a statement.** An entry named
`HORSE-RADISH SAUCE` that says "horse-radish" names its own subject. A mother
is exempt, because a mother is never an entry's own subject. `LENTEN
ESPAGNOLE` naming Espagnole does state its base.

**A name stated only inside a longer stated name is not a statement.** The
longer name shadows the shorter one when the two reach different
preparations. "Lenten Espagnole" states entry 24 and does not also state the
mother. When both names reach one preparation, the mother concept is
recorded, so `parent: bechamel` stays `bechamel`.

**Ambiguity still resolves to nothing.** Exactly one candidate in the
opening paragraph, or no parent. This rule now dissolves links the old rule
recorded. `ANDALOUSE SAUCE` names Mayonnaise sauce and tomato purée, and the
old rule read the purée as the mother Tomato. It records `None` now.

**A cycle is cleared, never broken by choice.** Two preparations deriving
from each other would make each its own ancestor. Every link on a cycle is
cleared, and links leading into it stay. Choosing one link to keep would be
an arbitrary choice wearing the costume of determinism.

**Half-glaze stays unencoded.** Bordelaise's opening names half-glaze and
never Espagnole. A term that encodes a derivation is not a statement of one,
so Bordelaise stays unresolved. That entry is the bar a later model measures
against, and this rule does not lower it.

## Consequences

### Positive

- Derived rises from 29 to 51, and unresolved falls from 95 to 73. All 24
  new links quote a name the source wrote in the opening paragraph.
- `saucier tree` gains depth. Marrow Sauce sits beneath Bordelaise, and
  Bordelaise itself still reports no parent.
- Two links the old rule recorded from ingredient words or compound phrases
  now dissolve to `None`, which is the honest reading.
- One link moves to the statement itself. Genevoise records Lenten
  Espagnole, where the old rule recorded the mother the name contains.

### Negative

- A recorded parent is no longer always a mother, so consumers must resolve
  a parent concept through the catalogue rather than a five-entry table.
- The subject and shadow rules are two more things a contributor must know
  before touching the matcher.
- A derivation stated under a name the catalogue does not carry, such as
  "the Bordelaise" alone, is still unresolved. The rule resolves less than a
  reader would, and that is the accepted trade.

## References

- [ADR-0002: An unresolved parent is recorded as absent, never inferred](0002-unresolved-is-not-none.md)
- [ADR-0007: The source decides what counts as a sauce](0007-the-source-classifies-its-own-contents.md)
- [Data model](../reference/data-model.md)
- [Glossary](../reference/glossary.md)
