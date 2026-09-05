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
  procedure  (unrecorded)
```

Cardinal states one base and one finish. The resolver reads names and cannot
tell them apart, so it refuses and prints what it saw. See
[ADR-0012](../adr/0012-a-resolver-may-refuse-never-rank.md).

Below the parent the command prints the procedure recorded for the
preparation, one operation per line, or `(unrecorded)` when none is. This
release records one, by hand, once per witness. See
[ADR-0017](../adr/0017-a-procedure-quotes-its-witness.md).

```console
$ uv run saucier show mornay
MORNAY SAUCE
entry 91, line 2437, transcription of escoffier-1909
  term  MORNAY SAUCE  [en]  mornay-sauce
  parent  bechamel
  procedure  6 operations, recorded by hand
    Boil      Béchamel Sauce [fr] 1 pint, fumet [fr] 1/4 pint
    Reduce    criterion: by a good quarter (unresolved)
    add       Gruyère [fr] 2 oz., Parmesan [en] 2 oz.
    Put       duration: a few minutes (unresolved), on the fire again
    stirring  instrument: small whisk, criterion: the melting of the cheese (unresolved)
    Finish    butter [en] 2 oz., away from the fire, added by degrees
```

Each line names the verb as the source writes it, then what the clause
states. Inputs come first, each with its language tag and its quantity.
Then the instrument, the criterion, the duration, and every constraint.
`(unresolved)` marks a parameter whose words give no number. Every word is
checked against the body before it is printed. A recorded procedure the
body does not state exits `2` and names the operation.

`--chars` sets how much prose to print. Default `600`. Prose that was cut
says so, and reports how much was left out.

Lookup accepts the full name or any whole run of words inside it, so
`bordelaise` finds `SAUCE BORDELAISE`. A preparation with alternative names
answers to all of them. `BROWN SAUCE OR ESPAGNOLE` is reachable as either.
When a name matches several preparations, the command prints the best match
and names the others on standard error.

Exit codes: `0` on success, `1` when no preparation matches. `2` when the
stored catalogue cannot be read, the name folds to nothing, or a recorded
procedure misquotes its body.

## `saucier export`

Loads the stored catalogue of every configured witness and writes the
interchange to standard output. One record per line, and nothing else on
that stream. Run `parse` first. The witnesses read their ids from the
corpus front matter, and the catalogues come from the store.

```console
$ uv run saucier export | head -n 1 | cut -c1-110
{"schema":"saucier/1","type":"catalogue","id":"escoffier-1909","work":"escoffier","edition":{"statement":"New
```

The stream holds two record types. Catalogue records come first, in the
configured order, then each catalogue's preparations in source order.
Every export writes every configured catalogue.
Identical catalogues produce identical bytes, so two exports of one `data/`
directory have one SHA-256. The record shapes are in the
[data model](data-model.md#interchange).

The stream is UTF-8 with no ASCII escaping, whatever the locale says. The
command sets the encoding on its own stream, so a latin-1 terminal cannot
make it fail on an em dash.

A reader that closes the pipe early, as `head` does, gets what it asked for
and the command exits `0`.

Exit codes: `0` on success, `2` when a stored catalogue cannot be read.
Standard output stays empty on failure, because every catalogue is loaded
before the first line is written.

## `saucier import --check`

Reads the interchange from standard input, rebuilds every catalogue in
memory, and prints the census. It writes no file. `--check` is mandatory in
this release, so the verb cannot imply a write the command does not perform.

```console
$ uv run saucier export | uv run saucier import --check
escoffier-1909  151 sauces, 57 derived, 94 unresolved
escoffier-1907  140 sauces, 50 derived, 90 unresolved
2 catalogues and 291 preparations rebuilt. Nothing written.
```

The reader consumes one line at a time, as UTF-8, and accepts records in
any order. Catalogues are rebuilt in the order their catalogue records
arrived. A catalogue record states how many preparations follow it, so a
stream cut at a line boundary is refused rather than rebuilt short. Two
complete exports cannot be joined, because the second repeats every id and
the reader rejects the first repeat. The reader rejects the first line it
cannot accept, and names the line:

```console
$ printf '{"schema":"saucier/2"}\n' | uv run saucier import --check
saucier: line 1: unknown schema 'saucier/2', this reader accepts 'saucier/1'
```

| Rejected | Message |
| --- | --- |
| Malformed JSON | `line 2: not JSON (Expecting value at column 31)` |
| Not UTF-8 | `line 2: not UTF-8 (invalid start byte at byte 9 of the line)` |
| A repeated key in one object | `line 2: object repeats a key: ['parent']` |
| A stream cut at a line boundary | `line 1: catalogue 'escoffier-1909' states 151 preparations, the stream carries 0` |
| A line that is not an object | `line 1: a record is a JSON object, not list` |
| Unknown schema | `line 1: unknown schema 'saucier/2', this reader accepts 'saucier/1'` |
| Unknown record type | `line 2: unknown record type 'claim'` |
| Missing or blank id | `line 1: a record needs an id` |
| Duplicate id | `line 3: duplicate id 'escoffier-1909:line:1317', first seen at line 2` |
| A second export joined to the first | `line 294: duplicate id 'escoffier-1909', first seen at line 1` |
| Catalogue never carried | `line 1: preparation names catalogue 'escoffier-1909', which the stream does not carry` |
| Unexpected or absent field | `line 2: preparation record fields: absent [], unexpected ['chapter']` |
| Blank parent | `line 2: surface form yields an empty concept id: ''` |
| Parent not a concept id | `line 2: 'Brown Roux' is not a concept id` |
| Concept not folded from the terms | `line 2: concept 'veloute' is not folded from the terms` |
| Id not the catalogue and line | `line 2: id 'escoffier-1909:entry:1' does not address 'escoffier-1909:line:1317'` |
| Catalogue id disagrees with its edition | `line 1: catalogue record 'escoffier-1800' describes 'escoffier-1909'` |
| Wrong value type | `line 1: expected a whole number, not '2963'` |
| A preparation citing another fidelity | `line 3: BROWN ROUX cites escoffier-1909 at ocr, in a catalogue at transcription` |

A `null` parent is unresolved and is accepted.

An empty stream fails. Without `pipefail` a pipeline returns the last
command's status. An empty stream is what a failed `export` leaves on the
other side of the pipe. The command refuses to report a success over
nothing:

```console
$ printf '' | uv run saucier import --check; echo $?
saucier: interchange carries no catalogues
2
```

Exit codes: `0` on success, `2` when the reader rejects a line or a rebuilt
catalogue, or the stream carries no catalogue. Without `--check` the parser
refuses the command and exits `2`.
