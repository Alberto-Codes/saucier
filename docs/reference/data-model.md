# Data model

Every entity is a frozen dataclass. Nothing in the domain performs IO.

## `Term`

A culinary term as one source writes it, in one language.

| Field | Type | Notes |
| --- | --- | --- |
| `surface` | `str` | Exactly as written. Never translated. |
| `language` | `Language` | ISO 639-1, inferred from the surface form. |
| `concept` | `ConceptId` | Language-independent identifier. |

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

`line` counts within the source body. The reader removes the Project Gutenberg
licence header and footer before it counts. The number is therefore not the
line number in the file on disk. For `escoffier-1907` that header is 24 lines,
so body line 2114 is file line 2138.

```console
$ sed -n '2138p' corpus/escoffier-1907.txt
64—BÉARNAISE TOMATÉE SAUCE OR CHORON SAUCE
```

## `Preparation`

One numbered entry. Carries its `title`, its `terms`, its unparsed `body`,
its `ref`, and its `parent`.

`parent` is `None` when the source states no mother. That is "unresolved", not
"has no mother" — the distinction matters, and the parser never guesses across
it.

## `Catalogue`

Everything read from one source, plus the `mothers` the source names for
itself.

| Member | Returns |
| --- | --- |
| `by_concept()` | Index by every name a preparation answers to |
| `find(concept)` | Lookup with a name-ending fallback |
| `children_of(concept)` | Derivations, in source order |
| `resolved` | Count of preparations with a parent |

## `Language`

ISO 639-1 codes for languages actually present in tracked sources. A member
is added when a source in that language is added, not in anticipation.
