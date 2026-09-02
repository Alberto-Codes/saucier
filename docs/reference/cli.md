# Command line reference

The `saucier` command has no runtime dependencies. It is built on `argparse`.

## `saucier parse`

Reads every committed witness, extracts a catalogue from each, writes it to
`data/<source-id>.json`, and reports a summary.

```console
$ uv run saucier parse
escoffier-1909  New and Revised Edition, January 1909 (impression: January 1920)
                transcription of Project Gutenberg 71395
                mothers: bechamel, espagnole, hollandaise, tomato, veloute
                151 sauces, 57 derived, 94 unresolved
escoffier-1907  no edition stated, copyright 1907
                ocr of Internet Archive cu31924000610117
                mothers: bechamel, espagnole, hollandaise, tomato, veloute
                140 sauces, 50 derived, 90 unresolved
```

| Line | Meaning |
| --- | --- |
| First | The source id, then the edition the document states |
| Second | How the text was obtained, and where from |
| `mothers` | Base preparations, as named by the source itself |
| Fourth | Sauces found, those linked to a stated parent, and those left unresolved |

The source id is read rather than configured. Neither line is taken from a
filename.

Exit codes: `0` on success, `2` when the source is unreadable, states no
edition, matches no entry pattern, or the catalogue cannot be written.

## `saucier diff OLDER NEWER`

Compares two stored catalogues and prints what caused each difference. Run
`parse` first, because it reads what is stored rather than the corpus.

The output has two sections. `names` reports concepts one witness holds and
the other does not. `parents` reports preparations whose recorded derivation
disagrees, whether the two witnesses call them by the same name or by two
names the diff paired.

Every row carries a cause, and a row may carry two.

| Cause | Meaning |
| --- | --- |
| `unmatched` | One witness holds it and the diff found no counterpart in the other |
| `added` | The later book has it and the earlier one does not |
| `removed` | The earlier book has it and the later one does not |
| `retitled` | One heading is the other plus whole words |
| `parent-changed` | A preparation records a different derivation in each witness |
| `ocr-suspected` | A scanned witness explains the row as well as a revision does |

`added` and `removed` state what a book contains, so they need an instrument
that can see everything in it. A scanned witness has a measured blind spot,
so a comparison involving one reports `unmatched` instead. See
[ADR-0014](../adr/0014-a-damaged-witness-cannot-establish-absence.md).

The summary prints the blind spot beside the counts: entries read from each
witness, and the gap between them. Against the committed corpus the gap is
284 entries, which is what an `unmatched` row cannot look past.

A scan can drop a heading's tail at a page break. So a `retitled` row also
carries `ocr-suspected` when a scanned witness is in the comparison. That
says the two readings cannot be told apart, not that one is right.

No row is adjudicated. `AURORE SAUCE` names two candidates in the proofread
text and one in the scan, because OCR destroyed an accent and hid a
candidate. The diff reports both readings and settles neither.

Exit codes: `0` on success, `2` when a stored catalogue cannot be read.

## `saucier tree CONCEPT [--source ID]`

Prints the derivation tree beneath a concept. Language tags after each title
show the language that title is written in.

```console
$ uv run saucier tree hollandaise
HOLLANDAISE SAUCE  [hollandaise]
├── MALTESE SAUCE  (en)
└── MOUSSELINE SAUCE  (en)
```

The bracket names the concept whose derivations follow, so the heading can
never caption a tree it does not belong to.

A root that states a parent of its own says so on the heading line. A mother
is what the source names as foundational, not a root of the tree.

```console
$ uv run saucier tree bordelaise
SAUCE BORDELAISE  [bordelaise]  derives from half-glaze
└── MARROW SAUCE  (en)
```

`--source` chooses the witness to read. It defaults to the revision, which is
`escoffier-1909`.

Exit codes: `0` on success, `1` when no preparation matches, `2` when the
stored catalogue cannot be read.

## `saucier show CONCEPT [--chars N] [--source ID]`

Prints one preparation. The output carries its title and its source entry and
line. It then lists every term with its language and concept id, the resolved
parent, and the opening of the prose.

An unresolved parent is followed by a `stated` line. It names every
candidate the opening paragraph states, in the order the paragraph
states them, or says `no candidate`.

```console
$ uv run saucier show cardinal-sauce
CARDINAL SAUCE
entry 69, line 2192, transcription of escoffier-1909
  term  CARDINAL SAUCE  [en]  cardinal-sauce
  parent  (unresolved)
  stated  bechamel, lobster-butter
```

Cardinal states one base and one finish. The resolver reads names and cannot
tell them apart, so it refuses and prints what it saw. See
[ADR-0012](../adr/0012-a-resolver-may-refuse-never-rank.md).

`--chars` sets how much prose to print. Default `600`. Prose that was cut
says so, and reports how much was left out.

Lookup accepts the full name or any whole run of words inside it, so
`bordelaise` finds `SAUCE BORDELAISE`. A preparation with alternative names
answers to all of them. `BROWN SAUCE OR ESPAGNOLE` is reachable as either.
When a name matches several preparations, the command prints the best match
and names the others on standard error.

Exit codes: `0` on success, `1` when no preparation matches, `2` when the
stored catalogue cannot be read or the name folds to nothing.
