# saucier

Structured procedure extraction from culinary sources.

Reads a cookbook and returns a catalogue. Each preparation carries its names,
the language of each name, the mother it derives from, and the source line the
claim came from. No model runs. Every output is traceable to the text.

## Try it

No GPU, no API key, no database, no network. The source text is committed.

```console
$ git clone https://github.com/Alberto-Codes/saucier
$ cd saucier && uv sync
$ uv run saucier parse
source      escoffier-1907
mothers     bechamel, espagnole, hollandaise, tomato, veloute
sauces      124
derived     29 linked to a mother
unresolved  95 state no base in their prose
```

The five mothers were not supplied. Escoffier names them in his own text, and
the parser reads them out of it.

```console
$ uv run saucier tree espagnole
BROWN SAUCE OR ESPAGNOLE  [espagnole]
├── LENTEN ESPAGNOLE  (fr)
├── GENEVOISE SAUCE  (en)
├── ORDINARY POIVRADE SAUCE  (en)
└── POIVRADE SAUCE FOR VENISON  (en)
```

## The interesting number is 95

Three quarters of these preparations never state what they are built on.
Escoffier wrote for a reader who already knew, so he did not write it down.
That gap is the point: it is the measured bar that anything cleverer has to
beat. See [why there is no model in this yet](https://alberto-codes.github.io/saucier/explanation/why-no-model-yet/).

The catalogue holds 124 entries, not every sauce in the book. An entry gets
in when its own heading says "sauce", or when it names a mother inside a
chapter Escoffier titles as sauces. Both tests read the source. Neither
guesses.

## Documentation

The rendered site is <https://alberto-codes.github.io/saucier/>. Its API
reference is generated from the docstrings, so it cannot drift from the code.

- [Tutorial](https://alberto-codes.github.io/saucier/tutorial/first-run/) — clone it and print a family tree
- [How-to](https://alberto-codes.github.io/saucier/how-to/add-a-source/) — point it at a different book
- [Reference](https://alberto-codes.github.io/saucier/reference/cli/) — commands and data model
- [Explanation](https://alberto-codes.github.io/saucier/explanation/why-no-model-yet/) — why a parser comes first
- [Decisions](https://alberto-codes.github.io/saucier/adr/) — the seven records, and what each one accepted

## Licence

MIT for the code. `corpus/escoffier-1907.txt` is Project Gutenberg ebook
#71395, public domain, redistributed with its licence wrapper intact. No
third-party corpus is shipped in the published package.
