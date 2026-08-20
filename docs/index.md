---
hide:
  - navigation
---

# saucier

Structured procedure extraction from culinary sources.

Reads a cookbook and returns a catalogue. Each preparation carries its names,
the language of each name, the mother it derives from, and the source line the
claim came from. No model runs. Every output is traceable to the text.

<p class="sc-stat" markdown>
<strong class="sc-figure">102</strong>
<span class="sc-caption">preparations out of 166 state no mother in their
prose. That gap is the measured bar, not a shortfall.</span>
</p>

```console
$ uv run saucier parse
source      escoffier-1907
mothers     bechamel, espagnole, hollandaise, tomato, veloute
sauces      166
derived     64 linked to a mother
unresolved  102 state no base in their prose
```

The five mothers were not supplied. Escoffier names his own base sauces in the
text, and the parser reads them out of that sentence.

<div class="grid cards" markdown>

-   :material-play-circle:{ .lg .middle } **Start here**

    ---

    Clone it and print a sauce family tree from a 1907 cookbook. No GPU, no
    key, no database, no network.

    [:octicons-arrow-right-24: First run](tutorial/first-run.md)

-   :material-tools:{ .lg .middle } **Point it somewhere else**

    ---

    Add a public-domain source, write an adapter, and find out whether the
    entry pattern fits.

    [:octicons-arrow-right-24: How-to guides](how-to/index.md)

-   :material-book-open-variant:{ .lg .middle } **Look something up**

    ---

    Commands, the data model, the glossary, and the API generated from the
    docstrings.

    [:octicons-arrow-right-24: Reference](reference/index.md)

-   :material-lightbulb-on:{ .lg .middle } **Understand the choices**

    ---

    Why a parser comes before a model, why four layers on a small codebase,
    and what the unresolved count is for.

    [:octicons-arrow-right-24: Explanation](explanation/index.md)

</div>

## What this is part of

`saucier` backs a blog series that ends with a robot making mole. Each
published post corresponds to a tag, and every tag runs and produces output.
This release is the first: a parser, no model, and a number to beat.
