# Your first run

By the end of this you will have printed a sauce derivation tree, built from
a cookbook revised in 1909, with nothing installed but Python.

## Before you start

You need Python 3.12 or newer and [uv](https://docs.astral.sh/uv/). You do
**not** need a GPU, an API key, a database, or a network connection — the
source text is committed to the repository.

## Get the code

```console
$ git clone https://github.com/Alberto-Codes/saucier
$ cd saucier
$ uv sync
```

## Read the book

```console
$ uv run saucier parse
```

You should see something like:

```
escoffier-1909  New and Revised Edition, January 1909 (impression: January 1920)
                transcription of Project Gutenberg 71395
                mothers: bechamel, espagnole, hollandaise, tomato, veloute
                151 sauces, 57 derived, 94 unresolved
escoffier-1907  no edition stated, copyright 1907
                ocr of Internet Archive cu31924000610117
                mothers: bechamel, espagnole, hollandaise, tomato, veloute
                140 sauces, 50 derived, 90 unresolved
```

Four things happened.

**Each source named itself.** `escoffier-1909` is not the filename. The
parser read the printing history off the title page and built the id from
it. You can read the same block:

```console
$ sed -n '119,123p' corpus/escoffier-1909.txt
        _First Printed, May 1907
     Second Impression, December 1907
  New and Revised Edition, January 1909
 New Impressions, August 1911, May 1913,
        March 1916, January 1920._
```

The five **mothers** were not supplied by us. Escoffier lists his own base
sauces, the parser found that sentence, and read them out of it.

**151 sauces** were extracted from roughly 3,000 numbered entries. The rest
are stocks, garnishes, soups, and dishes. An entry gets in when its heading
says "sauce", or when Escoffier filed it in a chapter he titles as sauces.

**94 unresolved** is the honest score, and it is the most interesting number
on the screen. A parser cannot read a derivation the author never wrote down,
and it will not choose between two he wrote.

The second block is a different book. `escoffier-1907` is a scan of the 1907
first printing, machine-read rather than proofread. Its numbers are lower,
and every record it produces says it came through OCR.

## Print a family tree

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

The tag after each name is the language its title is written in. The tree has
depth because a parent may be any catalogued preparation, not only a mother:
Robert states half glaze, and half glaze states Espagnole. Espagnole is a
mother, and it states brown roux, which the heading line says. Try
`brown-roux` to see the whole chain, or `hollandaise` and `veloute`.

## Look one up

```console
$ uv run saucier show bordelaise
SAUCE BORDELAISE
entry 32, line 1680, transcription of escoffier-1909
  term  SAUCE BORDELAISE  [fr]  sauce-bordelaise
  parent  half-glaze
  procedure  (unrecorded)
```

You asked for `bordelaise`. Escoffier writes `SAUCE BORDELAISE`, French word
order, and the lookup handled it.

Bordelaise states half glaze, and Marrow Sauce states Bordelaise:

```console
$ uv run saucier tree bordelaise
SAUCE BORDELAISE  [bordelaise]  derives from half-glaze
└── MARROW SAUCE  (en)
```

Now look at one the parser refused:

```console
$ uv run saucier show cardinal-sauce
CARDINAL SAUCE
entry 69, line 2192, transcription of escoffier-1909
  term  CARDINAL SAUCE  [en]  cardinal-sauce
  parent  (unresolved)
  stated  bechamel, lobster-butter
  procedure  (unrecorded)
```

Cardinal says "Boil one pint of Béchamel", and later "finish the sauce ...
with three oz. of very red lobster butter". One is the base and one is the
finish. The parser reads names and cannot tell which is which, so it records
nothing and prints both. The record keeps the claims apart: what the source
said, and what the parser could not decide.

Now check the parser's work. `line 1680` is a line in the file on disk:

```console
$ sed -n '1680p' corpus/escoffier-1909.txt
32—SAUCE BORDELAISE
```

Every claim in the output is traceable that way.

## Read a procedure

A parent says what a sauce is built from, and not what is done with it.
One preparation now says that too:

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

Six operations, in the order the body states them. The first one boils
one pint of Béchamel, which is the parent, so the derivation finally has
a verb. Every word on those lines is quoted from the entry, and the
command checks each one against the body before it prints. `a few
minutes` is a duration the text gives no number for, so its number is
unresolved. That is the same absence a parent records when the source
states none.

The scan states the same procedure in its own words. Its heading reads
`MORN AY SAUCE`, so look it up by that name:

```console
$ uv run saucier show morn-ay-sauce --source escoffier-1907
MORN AY SAUCE
entry 91, line 2864, ocr of escoffier-1907
  term  MORN AY SAUCE  [en]  morn-ay-sauce
  parent  (unresolved)
  stated  no candidate
  procedure  6 operations, recorded by hand
    Boil      Bdchamel Sauce [fr] 1 pint, fumet [fr] 1/4 pint
    Reduce    criterion: by a good quarter (unresolved)
    add       Gruy^re [fr] 2 oz., Parmesan [en] 2 oz.
    Put       duration: a few minutes (unresolved), on the fire again
    stirring  instrument: small whisk, criterion: the melting of the cheese (unresolved)
    Finish    butter [en] 2 oz., away from the fire, added by degrees
```

The scanner turned `Béchamel` into `Bdchamel`, so the scan's Mornay has
no parent it can name. The verb survived, and so did every quantity. Only
one preparation is recorded in this release, and a hand read it.
Everything else prints `(unrecorded)`.
[ADR-0017](../adr/0017-a-procedure-quotes-its-witness.md) says why one is
enough to settle the shape, and what the two witnesses disagree on.

## What you have

Two JSON catalogues under `data/`, one per witness, reproducible from the
committed corpus at any time. `data/` is not tracked, because anything in it
can be regenerated by running `parse` again.

## Carry it out of the process

The JSON files are a snapshot for this program. To hand the catalogue to
anything else, write it as one record per line:

```console
$ uv run saucier export > escoffier.jsonl
$ head -n 2 escoffier.jsonl
{"schema":"saucier/1","type":"catalogue","id":"escoffier-1909","work":"escoffier","edition":{"statement":"New and Revised Edition, January 1909","stated_year":1909,"impression":"January 1920","copyright_year":1907},"origin":"Project Gutenberg 71395","fidelity":"transcription","mothers":["bechamel","espagnole","hollandaise","tomato","veloute"],"preparations":151,"entries_read":2963}
{"schema":"saucier/1","type":"catalogue","id":"escoffier-1907","work":"escoffier","edition":{"statement":null,"stated_year":null,"impression":null,"copyright_year":1907},"origin":"Internet Archive cu31924000610117","fidelity":"ocr","mothers":["bechamel","espagnole","hollandaise","tomato","veloute"],"preparations":140,"entries_read":2679}
```

Every line says what it is, which schema shaped it, and which catalogue it
belongs to. The two catalogue records come first, each carrying the witness
it was read from, then one record per preparation. A preparation is
addressed by its catalogue and its heading line, so
`escoffier-1909:line:1680` is Bordelaise, and 1680 is the line you opened
with `sed` above.

```console
$ grep '"id":"escoffier-1909:line:1680"' escoffier.jsonl | cut -c1-160
{"schema":"saucier/1","type":"preparation","id":"escoffier-1909:line:1680","catalogue":"escoffier-1909","title":"SAUCE BORDELAISE","terms":[{"surface":"SAUCE BO
```

Prove the stream rebuilds both catalogues without writing anything:

```console
$ uv run saucier import --check < escoffier.jsonl
escoffier-1909  151 sauces, 57 derived, 94 unresolved
escoffier-1907  140 sauces, 50 derived, 90 unresolved
2 catalogues and 291 preparations rebuilt. Nothing written.
```

The same four numbers. Run `export` twice and compare the hashes. They are
identical, because the writer emits records in one order, with one key
order, and no timestamp. Feed the check an empty stream and it fails with
exit code 2, because an empty stream is what a failed export leaves behind
and a check must not call that a success. A serialization and a database are different
decisions, and
[ADR-0016](../adr/0016-jsonl-is-the-interchange-not-a-store.md) says why
this release makes only the first.

## Compare the two printings

```console
$ uv run saucier diff escoffier-1907 escoffier-1909
```

Every row carries a cause. `ocr-suspected` means one witness is a scan and
the difference may be the scanner rather than Escoffier. Nothing in the
output decides which. Read
[ADR-0010](../adr/0010-fidelity-is-a-property-of-the-record.md) for why the
record has to carry that distinction.

## Next

Read [why there is no model in this yet](../explanation/why-no-model-yet.md).
The 94 unresolved preparations are the reason there will be one.
