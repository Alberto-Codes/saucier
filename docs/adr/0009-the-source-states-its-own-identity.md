# ADR-0009: The source states its own identity, and a filename is not evidence

## Status

Accepted.

## Date

2026-08-21

## Context

`corpus/escoffier-1907.txt` is Project Gutenberg ebook 71395. Its title page
is transcribed in the file this project ships. It reads:

```
                        NEW AND REVISED EDITION

                        [Logo: Windmill, 1920]
                       LONDON: WILLIAM HEINEMANN

        _First Printed, May 1907
     Second Impression, December 1907
  New and Revised Edition, January 1909
 New Impressions, August 1911, May 1913,
        March 1916, January 1920._

_Copyright 1907 by William Heinemann._
```

The book is the January 1920 impression of the New and Revised Edition of
January 1909. `1907` is the copyright year on the verso. It is not the
edition.

Project Gutenberg's own metadata reads `London: William Neinemann, 1907,
pubdate 1920`. That field holds a copyright year and a printing year side by
side, and resolves to neither.

So `escoffier-1907` named an edition this project had never read. The
identifier is load-bearing. It is stamped into every provenance record, and
two published posts quote it.

The claims themselves were sound. The line numbers are right, the entries are
right, the derivations are right. The label on the book was wrong.

This is also ADR-0007 broken by its own author. ADR-0007 says the source
decides what counts as a sauce. The source states its edition more plainly
than it states anything else, on its own title page, and this project read a
filename instead.

## Decision

**A source reports the edition it states, and its `source_id` derives from
that reading.**

Four facts come out of the front matter, and they are recorded separately
because one string cannot carry four facts.

| Fact | Read from | Escoffier, Gutenberg 71395 |
| --- | --- | --- |
| Edition statement | A printing-history line naming an edition | `New and Revised Edition, January 1909` |
| Edition year | The year of that statement | 1909 |
| Impression | The last printing the history records | `January 1920` |
| Copyright year | The copyright line | 1907 |

**The edition statement decides the year. With no edition stated, the
copyright year decides it.** A revision announces itself in the printing
history. A first printing has no history to print. The Internet Archive
witness of the 1907 first printing states no edition. Its year is the
copyright year it does print.

**A source that states neither is unreadable.** `read_edition` raises
`EditionUnstated` rather than falling back to the path. A document with no
stated identity is a situation to report.

**A `source_id` is the work name and the edition year, joined.** The work
name is configured, because a title page names a book rather than a
repository. The year is read. `escoffier` plus 1909 gives `escoffier-1909`.

**The corpus filename is renamed to agree, and a test proves the agreement.**
`tests/test_corpus.py` asserts that each corpus file is named for the
`source_id` read out of it. The filename is a convenience for a reader with a
shell. It is never the evidence.

## Consequences

### Positive

- The catalogue names the edition it parsed. `escoffier-1909` is checkable
  against the title page in the same file.
- `escoffier-1907` is free for the 1907 first printing, which ADR-0010 adds.
- Adding a second edition of one work needs no new identifier scheme. Two
  witnesses of two editions get two ids, from two title pages.
- A corpus file swapped for a different printing fails a test rather than
  publishing a wrong citation.

### Negative

- Every published provenance claim that names `escoffier-1907` now names the
  1909 revision under its old label. The correction is a release note and a
  post, not a silent edit.
- Reading the front matter costs one pass over the head of the file before
  any extraction runs.
- The rule is Escoffier-shaped. A source whose printing history uses another
  layout reads as unstated, and `read_edition` raises rather than guessing.
- The 1909 census is unchanged at 124 sauces, 50 derived, and 74 unresolved.
  A reader who only sees the identifier change may read the release as
  cosmetic.

## References

- [ADR-0007: The source decides what counts as a sauce](0007-the-source-classifies-its-own-contents.md)
- [ADR-0010: Fidelity is a property of the record](0010-fidelity-is-a-property-of-the-record.md)
- [Glossary](../reference/glossary.md)
