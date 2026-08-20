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
sauces      166
derived     64 linked to a mother
unresolved  102 state no base in their prose
```

The five mothers were not supplied. Escoffier names them in his own text, and
the parser reads them out of it.

```console
$ uv run saucier tree espagnole
BROWN SAUCE OR ESPAGNOLE  [espagnole]
├── LENTEN ESPAGNOLE  (en)
├── GENEVOISE SAUCE  (en)
├── ORDINARY POIVRADE SAUCE  (en)
└── POIVRADE SAUCE FOR VENISON  (en)
```

## The interesting number is 102

Two thirds of these preparations never state what they are built on.
Escoffier wrote for a reader who already knew, so he did not write it down.
That gap is the point: it is the measured bar that anything cleverer has to
beat. See [why there is no model in this yet](docs/explanation/why-no-model-yet.md).

## Documentation

- [Tutorial](docs/tutorial/first-run.md) — clone it and print a family tree
- [How-to](docs/how-to/add-a-source.md) — point it at a different book
- [Reference](docs/reference/cli.md) — commands and data model
- [Explanation](docs/explanation/why-no-model-yet.md) — why a parser comes first

## Licence

MIT for the code. `corpus/escoffier-1907.txt` is Project Gutenberg ebook
#71395, public domain, redistributed with its licence wrapper intact. No
third-party corpus is shipped in the published package.
