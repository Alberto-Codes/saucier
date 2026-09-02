# saucier

Structured procedure extraction from culinary sources.

Reads a cookbook and returns a catalogue. Each preparation carries its names,
the language of each name, the parent it derives from, and the source line the
claim came from. No model runs. Every output is traceable to the text.

## Try it

No GPU, no API key, no database, no network. Both source texts are committed.

```console
$ git clone https://github.com/Alberto-Codes/saucier
$ cd saucier && uv sync
$ uv run saucier parse
escoffier-1909  New and Revised Edition, January 1909 (impression: January 1920)
                transcription of Project Gutenberg 71395
                mothers: bechamel, espagnole, hollandaise, tomato, veloute
                151 sauces, 57 derived, 94 unresolved
escoffier-1907  no edition stated, copyright 1907
                ocr of Internet Archive cu31924000610117
                mothers: bechamel, espagnole, hollandaise, tomato, veloute
                140 sauces, 49 derived, 91 unresolved
```

The five mothers were not supplied. Escoffier names them in his own text, and
the parser reads them out of it.

Neither is the edition supplied. Each source states its own printing history
on its own title page, and the id is built from that reading. See
[ADR-0009](docs/adr/0009-the-source-states-its-own-identity.md).

```console
$ uv run saucier tree espagnole
BROWN SAUCE OR ESPAGNOLE  [espagnole]  derives from brown-roux
├── HALF GLAZE  (en)
│   ├── SAUCE BORDELAISE  (fr)
│   │   └── MARROW SAUCE  (en)
│   ├── BROWN CHAUD-FROID SAUCE  (en)
│   ├── DEVILLED SAUCE  (en)
│   ├── ITALIAN SAUCE  (en)
│   ├── LYONNAISE SAUCE  (en)
│   ├── MADEIRA SAUCE  (en)
│   ├── PIQUANTE SAUCE  (en)
│   └── ROBERT SAUCE  (en)
├── LENTEN ESPAGNOLE  (fr)
│   └── GENEVOISE SAUCE  (en)
├── ORDINARY POIVRADE SAUCE  (en)
└── POIVRADE SAUCE FOR VENISON  (en)
```

A parent may be any catalogued preparation, not only a mother. Robert states
half glaze, half glaze states Espagnole, and Espagnole states brown roux. A
mother is what the source names as foundational, and two of the five now
state a parent of their own.

## The interesting number is 94

94 of 151 preparations state no base in their opening paragraph, or state
two and mark neither. Escoffier wrote for a reader who already knew, so he
did not write it down. That gap is the point: it is the measured bar that
anything cleverer has to beat. See
[why there is no model in this yet](https://alberto-codes.github.io/saucier/explanation/why-no-model-yet/).

The catalogue holds 151 entries, not every sauce in the book. An entry gets
in when its own heading says "sauce", or when Escoffier filed it in a chapter
he titles as sauces. Both tests read the source. Neither guesses.

Derived rose from 50 to 57 in this release, and that seven is three numbers.
Twelve sauces gained the parent Escoffier wrote, most of them half glaze. Ten
lost one, because a catalogued butter now sits in their opening paragraph
beside the base, and a resolver may refuse, never rank. Five admitted entries
state a parent. `saucier show cardinal-sauce` prints both names it saw. See
[ADR-0015](docs/adr/0015-the-chapter-decides.md).

## Two witnesses, and a diff that names its causes

The corpus holds two texts of one book. One is proofread and one is a raw
scan, so every difference between them has two explanations.

```console
$ uv run saucier diff escoffier-1907 escoffier-1909
...
  11 unmatched, 20 parent-changed, 37 ocr-suspected
  entries read  2679 of escoffier-1907, 2963 of escoffier-1909, a blind spot of 284
```

`QENEVOISE SAUCE` is `GENEVOISE SAUCE` with one letter misread, and the diff
says so rather than reporting a removal it cannot support.

It reports no additions at all. The 1907 witness is a scan and 284 of its
entries are unread. So a concept found in one witness and not the other is
`unmatched` rather than added. **No editorial difference between the two
printings has been confirmed.** Every candidate so far has been the scanner
or the reader.

## Documentation

The rendered site is <https://alberto-codes.github.io/saucier/>. Its API
reference is generated from the docstrings, so it cannot drift from the code.

- [Tutorial](https://alberto-codes.github.io/saucier/tutorial/first-run/) — clone it and print a family tree
- [How-to](https://alberto-codes.github.io/saucier/how-to/add-a-source/) — point it at a different book
- [Reference](https://alberto-codes.github.io/saucier/reference/cli/) — commands and data model
- [Explanation](https://alberto-codes.github.io/saucier/explanation/why-no-model-yet/) — why a parser comes first
- [Decisions](https://alberto-codes.github.io/saucier/adr/) — the fifteen records, and what each one accepted

## Licence

MIT for the code.

`corpus/escoffier-1909.txt` is Project Gutenberg ebook #71395, public domain,
redistributed with its licence wrapper intact. It transcribes the January
1920 impression of the New and Revised Edition of January 1909.

`corpus/escoffier-1907.txt` is Internet Archive item `cu31924000610117`, the
Cornell University Library copy of the 1907 first printing. Cornell records
no known United States copyright restrictions on the text, and a 1907
publication date puts it in the public domain.

No third-party corpus is shipped in the published package.
