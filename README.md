# saucier

Structured procedure extraction from culinary sources.

Reads a cookbook and returns a catalogue. Each preparation carries its names,
the language of each name, the parent it derives from, and the source line the
claim came from. No model runs. Every output is traceable to the text.

## Try it

No GPU, no API key, no database, no network. The source text is committed.

```console
$ git clone https://github.com/Alberto-Codes/saucier
$ cd saucier && uv sync
$ uv run saucier parse
escoffier-1909  New and Revised Edition, January 1909 (impression: January 1920)
                transcription of Project Gutenberg 71395
                mothers: bechamel, espagnole, hollandaise, tomato, veloute
                124 sauces, 50 derived, 74 unresolved
escoffier-1907  no edition stated, copyright 1907
                ocr of Internet Archive cu31924000610117
                mothers: bechamel, espagnole, hollandaise, tomato, veloute
                102 sauces, 32 derived, 70 unresolved
```

The five mothers were not supplied. Escoffier names them in his own text, and
the parser reads them out of it.

Neither is the edition supplied. Each source states its own printing history
on its own title page, and the id is built from that reading. See
[ADR-0009](docs/adr/0009-the-source-states-its-own-identity.md).

```console
$ uv run saucier tree espagnole
BROWN SAUCE OR ESPAGNOLE  [espagnole]
├── LENTEN ESPAGNOLE  (fr)
│   └── GENEVOISE SAUCE  (en)
├── ORDINARY POIVRADE SAUCE  (en)
│   └── REFORM SAUCE  (en)
└── POIVRADE SAUCE FOR VENISON  (en)
```

A parent may be any catalogued preparation, not only a mother. Marrow Sauce
resolves to Bordelaise, and Bordelaise itself states no base. A derivation
tree can therefore root in an unresolved sauce.

## The interesting number is 74

74 of 124 preparations never state what they are built on. Escoffier wrote
for a reader who already knew, so he did not write it down. That gap is the
point: it is the measured bar that anything cleverer has to beat. See
[why there is no model in this yet](https://alberto-codes.github.io/saucier/explanation/why-no-model-yet/).

The catalogue holds 124 entries, not every sauce in the book. An entry gets
in when its own heading says "sauce", or when it names a mother inside a
chapter Escoffier titles as sauces. Both tests read the source. Neither
guesses.

## Two witnesses, and a diff that names its causes

The corpus holds two texts of one book. One is proofread and one is a raw
scan, so every difference between them has two explanations.

```console
$ uv run saucier diff escoffier-1907 escoffier-1909
...
  20 added, 12 parent-changed, 27 ocr-suspected
```

Fifteen names look removed and a scanner explains every one of them.
`QENEVOISE SAUCE` is `GENEVOISE SAUCE` with one letter misread. The diff
says so rather than reporting a removal it cannot support. It never decides
which witness is right.

## Documentation

The rendered site is <https://alberto-codes.github.io/saucier/>. Its API
reference is generated from the docstrings, so it cannot drift from the code.

- [Tutorial](https://alberto-codes.github.io/saucier/tutorial/first-run/) — clone it and print a family tree
- [How-to](https://alberto-codes.github.io/saucier/how-to/add-a-source/) — point it at a different book
- [Reference](https://alberto-codes.github.io/saucier/reference/cli/) — commands and data model
- [Explanation](https://alberto-codes.github.io/saucier/explanation/why-no-model-yet/) — why a parser comes first
- [Decisions](https://alberto-codes.github.io/saucier/adr/) — the twelve records, and what each one accepted

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
