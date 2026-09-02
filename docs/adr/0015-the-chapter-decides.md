# ADR-0015: The chapter decides

## Status

Accepted.

## Date

2026-09-01

## Context

ADR-0007 admits an entry on two kinds of evidence. The heading says "sauce".
Or the source filed the entry in a chapter it titles as sauces, and the
heading also names a mother.

That second test has two clauses. The chapter clause reads the source's own
classification. The mother clause adds a test of ours on top of it, and the
added test overrules the reading.

`ROBERT SAUCE` says "add one pint of half-glaze". `HALF GLAZE` is entry 23,
at line 1437 of the 1909 text. It sits inside the chapter Escoffier titles
`THE LEADING WARM SAUCES`. Its heading names no mother, so the mother clause
kept it out of the catalogue, and Robert stayed unresolved.

The three sauce chapters of the 1909 text hold 139 numbered entries. 29 of
them lack the word "sauce" in the heading. Two entered on the mother clause,
`LENTEN ESPAGNOLE` and `VELOUTÉ DE VOLAILLE`. The other 27 stayed out. They
are the three roux, half glaze, two gravies, a lobster method numbered as
its own entry, whisked mayonnaise, and various cullises. The remaining 18 are
compound butters, in a chapter titled `COLD SAUCES AND COMPOUND BUTTERS`.

The veto had a cost the census did not show. Eleven sauces state half glaze
as their base. Five entries state a roux. The book writes the chain from
brown roux to Espagnole, from Espagnole to half glaze, and from half glaze to
Robert. The catalogue dropped the middle link.

## Decision

**An entry inside a sauce chapter qualifies on the chapter. An entry outside
one qualifies on its heading alone.**

**The source's classification is not second-guessed.** When the source has
already classified an entry, a second test is a veto, not a check. The mother
clause is removed. `is_sauce` reads the heading, then the chapter, and
nothing else.

**The heading test stays as the first check everywhere.** Inside a sauce
chapter it changes nothing. Outside one it is the only evidence, which is how
the sweet sauces in the entremets chapter enter.

**Chapter I stays out.** `FONDS DE CUISINE` holds stocks, essences, and
glazes, entries 7 to 18. Escoffier does not title it as sauces. Espagnole
names brown stock and the catalogue cannot see it. That is a later record.

**Nothing is hand-excluded.** `SECOND METHOD (WITH COOKED LOBSTER)` is entry
97 and `VARIOUS CULLISES` is entry 144. The source numbered both inside a
sauce chapter, so both enter. An admitted entry that reads oddly as a
preparation is a finding, never a special case in the parser.

**A mother may have a parent.** Escoffier names five mothers, and that does
not change. Espagnole now states brown roux, and Velouté states pale roux.
Both stop being roots of the tree, and `saucier tree` says so on its heading
line.

**An unresolved parent is printed with what it states.** `saucier show`
names the candidates the opening paragraph states beside an unresolved
parent. A reader sees why the resolver refused, in the order the paragraph
states the names.

## Consequences

### Positive

- The 1909 census moves from 124 sauces, 50 derived, 74 unresolved to 151
  sauces, 57 derived, 94 unresolved. 27 entries enter.
- The 1907 census moves from 115, 36, 79 to 140, 49, 91. 25 entries enter.
  `MONTPELLIER BUTTER` and `HAZEL-NUT BUTTER` do not, because the scan reads
  their numbers as `IS3` and `15s`, and the entry pattern never matches. A
  corrupted number is structure, and ADR-0013 leaves its repair to a separate
  decision.
- Twelve sauces gain the parent Escoffier wrote. Eight resolve to half glaze:
  `SAUCE BORDELAISE`, `BROWN CHAUD-FROID SAUCE`, `DEVILLED SAUCE`, `ITALIAN
  SAUCE`, `LYONNAISE SAUCE`, `MADEIRA SAUCE`, `PIQUANTE SAUCE`, and `ROBERT
  SAUCE`. Espagnole resolves to brown roux, Velouté to pale roux, and `SCOTCH
  EGG SAUCE` to white roux. `MOUSSEUSE SAUCE` resolves to manied butter.
- Five of the 27 admitted entries state a parent. Half glaze resolves to
  Espagnole, pale roux to brown roux, white roux to pale roux, `VEAL GRAVY
  TOMATÉ` to tomato, and `WHISKED MAYONNAISE` to horse-radish.
- The chain above Robert is three links long, and four with the roux. Robert
  states half glaze, half glaze states Espagnole, and Espagnole states brown
  roux. No chain cycles. Brown roux states nothing, pale roux states brown,
  and white roux states pale.

### Negative

- Ten sauces that were resolved at v0.3.0 are unresolved. Seven lose their
  parent to a compound butter: `CARDINAL SAUCE`, `NANTUA SAUCE`, `NOISETTE
  SAUCE`, `DIPLOMATE SAUCE`, `JOINVILLE SAUCE`, `HERB SAUCE`, and `RAVIGOTE
  SAUCE`. Three lose it to half glaze: `PÉRIGUEUX SAUCE`, `REFORM SAUCE`, and
  `CHASSEUR SAUCE`. Each now states a second catalogued candidate.
- Cardinal is the shape of the loss. It says "Boil one pint of Béchamel" and
  then "finish the sauce ... with three oz. of very red lobster butter". The
  source stated one base and one finish. The resolver reads names and cannot
  tell the two apart, so ADR-0012 refuses. The refusal is correct under the
  rule as written. Recovering the ten means reading the verb a name sits in,
  which is a later record. The candidate rule is not tuned to save the
  number.
- Derived rose by seven, and that seven is three numbers. Twelve sauces
  gained a parent, ten lost one, and five admitted entries state one. A
  reader who sees only the seven sees a gain that hides a loss.
- Two admitted entries resolve on a name the sentence uses for an
  ingredient. `WHISKED MAYONNAISE` resolves to horse-radish because
  `HORSE-RADISH OR ALBERT SAUCE` lends the bare name `horse-radish`, and the
  paragraph names rasped horse-radish among the ingredients. `MOUSSEUSE
  SAUCE` resolves to manied butter because "stiffly-manied butter" carries the
  name of entry 151. Both are the name rule working as written. Whether
  either statement is a derivation is a question for the verb reader, and
  this record leaves both as findings.
- The 1907 scan reads the number of `WHISKED MAYONNAISE` as `138`, which is
  also the number of `HORSE-RADISH SAUCE`. The resolver keys its bookkeeping
  on the entry number, so the later preparation's result overwrites the
  first. Whisked mayonnaise resolves to horse-radish on its own and records
  unresolved. Entry 63 already shared a number at v0.3.0 with no visible
  effect. This is a corrupted number, and this record leaves it where
  ADR-0013 left it.
- Three parents now differ between the witnesses for one reason. `HERB
  SAUCE`, `RAVIGOTE SAUCE`, and `PÉRIGUEUX SAUCE` state two candidates in the
  proofread text and refuse. The scan hides one candidate in each, so the
  scan answers. That is the Aurore shape from ADR-0012, three more times.
- Sweet sauces still enter on their headings only. ADR-0007's last negative
  consequence stands.

## References

- [ADR-0002: An unresolved parent is recorded as absent, never inferred](0002-unresolved-is-not-none.md)
- [ADR-0007: The source decides what counts as a sauce](0007-the-source-classifies-its-own-contents.md)
- [ADR-0012: A resolver may refuse, never rank](0012-a-resolver-may-refuse-never-rank.md)
- [ADR-0013: Normalisation repairs structure, never content](0013-repair-structure-never-content.md)
- [Glossary](../reference/glossary.md)
