# Data model

Every entity is a frozen dataclass. Nothing in the domain performs IO.

## How one source becomes a catalogue

`saucier.services.extraction` makes every entity below in two passes. The
first pass reads the mothers, the sauce chapters, and every kept entry. The
second pass resolves each parent against every name the first pass produced.
The candidates are therefore read out of the source, not supplied to it.

```mermaid
flowchart TD
    accTitle: How one source becomes a catalogue
    accDescr {
        The source reader yields lines, and three steps read them.
        find_mothers scans the whole body once and returns the concepts the
        source calls basic sauces. sauce_chapters reads the chapter titles and
        returns the line spans of the chapters the source titles as sauces.
        iter_entries walks the same lines and yields one numbered entry at a
        time. is_sauce tests each entry heading, keeps it when the heading
        itself says sauce, and otherwise keeps it only when the heading names a
        mother inside a sauce chapter. A rejected entry stays out of the
        catalogue. terms_in splits a kept heading into one language-tagged Term
        per alternative name. parent_candidates collects every name of every
        kept preparation, plus the mothers. resolve_parent reads the opening
        paragraph only, and sets the parent to the single candidate that
        paragraph states, or to None when it states none or states more than
        one. A cycle of stated parents is cleared. The result is a
        Catalogue of 124 preparations, 51 resolved and 73 unresolved.
    }

    lines(["source.lines()"]) --> entries["iter_entries<br/>one numbered entry"]
    entries --> sauce{"is_sauce<br/>heading says sauce,<br/>or names a mother<br/>in a sauce chapter?"}
    sauce -->|yes| terms["terms_in<br/>one Term per name"]
    terms --> names["parent_candidates<br/>every kept name"]
    names --> parent["resolve_parent<br/>opening paragraph only,<br/>one candidate or none"]
    parent --> cat(["Catalogue<br/>124 preparations<br/>73 unresolved"])
    sauce -->|no| drop(["stays out of the catalogue"])
    lines --> mothers["find_mothers<br/>whole body, once"]
    lines --> chapters["sauce_chapters<br/>chapter titles"]
    mothers --> sauce
    chapters --> sauce
    mothers --> names
```

<details markdown="1">
<summary>The same pipeline in text</summary>

1. The source reader yields the body as lines.
2. `find_mothers` scans the whole body once. It returns the concepts the
   source itself calls basic sauces.
3. `iter_entries` walks the same lines. It yields one numbered entry at a
   time.
4. `sauce_chapters` reads the chapter titles. It returns the line spans of
   the chapters the source titles as sauce chapters.
5. `is_sauce` keeps a heading that says "sauce" before any "with". It
   otherwise keeps a heading only when the heading names a mother and the
   entry sits inside a sauce chapter.
6. A rejected entry stays out of the catalogue.
7. `terms_in` splits a kept heading into one `Term` per alternative name, each
   tagged with its language.
8. `parent_candidates` collects every name a stated parent may use. The names
   are every term of every kept preparation, plus the mothers.
9. `resolve_parent` reads the opening paragraph only. It sets the parent to
   the single candidate that paragraph states. It sets `None` when the
   paragraph states none, and also when it states more than one.
10. A cycle of stated parents is cleared, so no preparation is its own
    ancestor.
11. The result is a `Catalogue` of 124 preparations. 51 resolve to a stated parent
    and 73 are unresolved.

</details>

## `Term`

A culinary term as one source writes it, in one language.

| Field | Type | Notes |
| --- | --- | --- |
| `surface` | `str` | Exactly as written. Never translated. |
| `language` | `Language` | ISO 639-1, inferred from the surface form. |
| `concept` | `ConceptId` | Derived from `surface`, not stored beside it. |

Terms are never translated. `mole` is not "sauce". `nixtamal` is not "corn".
Translating a term destroys the distinction the term exists to carry, so
surface forms are preserved and tagged instead.

## `ConceptId`

A folded identifier: diacritics stripped, lowercased, punctuation collapsed
to hyphens. `Velouté` and `VELOUTE` reach `veloute`.

Folding resolves **orthographic** variation only. It does not resolve semantic
equivalence across languages. Deciding that `salsa española` and `espagnole`
denote one concept requires evidence, not string manipulation.

## `SourceRef`

Where a preparation was found: `source_id`, the source's own `entry` number,
and the `line` it begins on. Every extracted claim carries one, so any output
can be checked against the text by hand.

`line` is the line number in the file on disk. The reader strips the Project
Gutenberg licence header, then adds the stripped line count back. The number
needs no adjustment:

```console
$ sed -n '2138p' corpus/escoffier-1907.txt
64—BÉARNAISE TOMATÉE SAUCE OR CHORON SAUCE
```

`entry` and `line` are keyword-only, and both must be 1 or greater. Two
integers side by side invite a transposition, and a transposed citation
points a reader at the wrong text while still type-checking.

`escoffier-1907` is [*A Guide to Modern Cookery*](https://www.gutenberg.org/ebooks/71395)
by A. Escoffier. The copy under `corpus/` is Project Gutenberg ebook 71395,
released on 2023-08-12. A `source_id` names an edition, not a work, because
two editions of one book number their entries differently.

## `Preparation`

One numbered entry. Carries its `title`, its `terms`, its unparsed `body`,
its `ref`, and its `parent`.

`parent` may name a mother or any catalogued preparation. When the opening
paragraph states a mother, the mother concept is recorded. Otherwise the
parent preparation's own concept is. Chains never cycle, because the
extractor clears every link on a cycle.

`parent` is `None` when the source states no base. That is "unresolved", not
"has no parent". The distinction matters, and the parser never guesses across
it. `parent` has no default, so every construction site states the absence
rather than inheriting it.

An entry whose opening paragraph states two candidates is also unresolved.
The source named both and chose neither, so the parser records no choice.

## `Catalogue`

Everything read from one source, plus the `mothers` the source names for
itself.

| Member | Returns |
| --- | --- |
| `by_concept()` | Index by every name a preparation answers to |
| `matches(concept)` | Every preparation a name could mean, best first |
| `find(concept)` | The best match, or `None` |
| `children_of(concept)` | Derivations, in source order |
| `resolved` | Count of preparations with a parent |
| `unresolved` | Count of preparations without one. The published score |

`matches` takes an exact hit outright. Otherwise the name has to appear as a
whole run of words, so `bordelaise` reaches `SAUCE BORDELAISE` and never
`bordelaise-butter`. Candidates are ordered by how little else their name
carries, then by source order. Both signals come from the source: the least
qualified name is the base, and Escoffier states a base before its
derivatives.

## `Language`

[ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes)
codes for languages actually present in tracked sources. A member is added
when a source in that language is added, not in anticipation. The tracked
corpus is English and French, so those are the two members.
