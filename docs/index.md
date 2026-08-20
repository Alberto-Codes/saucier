---
hide:
  - navigation
---

# saucier

Structured procedure extraction from culinary sources.

`saucier` reads a cookbook and returns a catalogue. Each preparation carries
its terms, the language of each term, the mother it derives from, and the
source line the claim came from. No model runs.

<div class="sc-specimen">
<p class="sc-specimen__label">One preparation, as the catalogue holds it</p>
<p class="sc-term"><span class="sc-term__surface">BÉARNAISE TOMATÉE SAUCE</span><span class="sc-term__lang">fr</span></p>
<p class="sc-term"><span class="sc-term__surface">CHORON SAUCE</span><span class="sc-term__lang">en</span></p>
<p class="sc-specimen__rel"><span class="sc-specimen__key">derives from</span><span class="sc-mother" data-mother="tomato">tomato</span></p>
<p class="sc-specimen__ref"><span class="sc-specimen__key">source</span> escoffier-1907 &nbsp;·&nbsp; <span class="sc-specimen__key">entry</span> <b>64</b> &nbsp;·&nbsp; <span class="sc-specimen__key">line</span> <b>2138</b></p>
</div>

One preparation, two terms, two languages. Neither term is translated into the
other, and both are kept exactly as Escoffier set them. `BÉARNAISE` folds to
`bearnaise` to give the concept its id, and the accented surface form is what
the catalogue stores. The citation is the point: entry 64 at line 2138 is a
line you can open in `corpus/` and read. The source is Escoffier's
[*A Guide to Modern Cookery*](https://www.gutenberg.org/ebooks/71395), tracked
here in full.

## The five mothers

Escoffier names his own foundational sauces in his own text. The parser reads
them out of that sentence. Nobody supplied the list.

<ul class="sc-mothers">
<li class="sc-mother" data-mother="bechamel">bechamel</li>
<li class="sc-mother" data-mother="espagnole">espagnole</li>
<li class="sc-mother" data-mother="hollandaise">hollandaise</li>
<li class="sc-mother" data-mother="tomato">tomato</li>
<li class="sc-mother" data-mother="veloute">veloute</li>
</ul>

## The number this release is judged on

<div class="sc-census">
<div class="sc-census__bar" role="img" aria-label="Of 124 preparations, 29 resolve to a mother and 95 are unresolved."><span class="sc-census__seg--resolved"></span><span class="sc-census__seg--unresolved"></span></div>
<ul class="sc-census__key">
<li><b>124</b> preparations</li>
<li><b>29</b> resolved</li>
<li><b>95</b> unresolved</li>
</ul>
</div>

95 preparations state no mother in their prose. The parser records those as
unresolved and does not guess at them. The hatched share is what the source
declined to say, not what the extraction failed to find. Lowering that count
by guessing would be the one unrecoverable mistake here, so the number is
published rather than hidden.

An entry that names two mothers counts as unresolved. `SHRIMP SAUCE` says
"fish velouté or, failing this, Béchamel". The source declined to choose, so
the parser declines too.

```console
$ uv run saucier parse
source      escoffier-1907
mothers     bechamel, espagnole, hollandaise, tomato, veloute
sauces      124
derived     29 linked to a mother
unresolved  95 state no base in their prose
```

## Where to go

<div class="sc-pointers" markdown>

[First run](tutorial/first-run.md)
:   Clone the repository and print a derivation tree from a 1907 cookbook. No
    GPU, no key, no database, no network.

[Add a source](how-to/add-a-source.md)
:   Point the extractor at another public-domain book, and find out whether
    the entry pattern fits it.

[Reference](reference/index.md)
:   The commands, the data model, the glossary, and the API generated from the
    docstrings.

[Explanation](explanation/index.md)
:   Why a parser comes before a model, why four layers on 900 lines, and what
    the unresolved count is for.

[Decisions](adr/index.md)
:   The architecture decision records, each with a status and a date.

</div>

## What this is part of

`saucier` backs a blog series that ends with a robot making mole. Each
published post corresponds to a tag, and every tag runs and produces output.
This release is the first: a parser, no model, and a number to beat.
