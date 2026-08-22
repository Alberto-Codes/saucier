# ADR-0011: Normalisation is an adapter that wraps a source

## Status

Accepted.

## Date

2026-08-21

## Context

The Internet Archive text does not match the extraction patterns as it
stands. Three of the parser's anchors were measured against the raw file:

| Anchor | Gutenberg 71395 | Archive, raw | Archive, normalised |
| --- | --- | --- | --- |
| `ENTRY` | 2963 | 2622 | 2622 |
| `CHAPTER` | 23 | 0 | 45 |
| `MOTHERS` | matches | no match | matches |

Neither failure is a comprehension problem. `CHAPTER` fails on a trailing
space in `CHAPTER  I `. `MOTHERS` fails on a space before the colon in
`basic  sauces :`. Three lines of whitespace and punctuation handling fix
both:

```python
line = re.sub(r"[ \t]+", " ", line)
line = re.sub(r"\s+([:;,.])", r"\1", line)
line = line.strip()
```

Three lines, and three bad homes for them.

**Inside the source adapter.** Every future source reimplements it, slightly
differently, and the differences are invisible until a census moves.

**Inside the extraction service.** The service now knows what OCR is, and
`lint-imports` cannot tell that a source-specific rule crossed a boundary.

**In a new layer between adapters and services.** The hexagon grows a fifth
layer to hold three lines, and every reader of ADR-0005 asks why.

Document pipelines grow a normalisation stage. It usually lands in one of
those three places, where it is source-specific and nobody can see it.

## Decision

**Normalisation is a driven adapter that implements `SourceText` and wraps
another `SourceText`.**

`NormalisedText` takes a source, delegates its witness and its line offset,
and maps every line through the rules above.

```python
source = NormalisedText(PlainText(path, work="escoffier", ...))
```

That answers all three objections at once.

**It lives in the adapter layer**, so the service and the domain learn
nothing about OCR.

**No future source reimplements it**, because it wraps any source rather than
living inside one. A second scanned book composes the same wrapper.

**It adds no layer**, because it satisfies the port it consumes. The hexagon
is unchanged and `lint-imports` needs no new contract.

**Normalisation preserves the line count.** Each rule maps one line to one
line, so a recorded line number still names a line in the file on disk. A
rule that joins or drops lines does not belong here.

**Normalisation never repairs a character.** It handles whitespace and the
space before punctuation. Restoring `velout^` to `velouté` would manufacture
agreement between the exact two witnesses this release compares.

*Amended by [ADR-0013](0013-repair-structure-never-content.md) in the same
release.* The line belongs between structure and content rather than at the
character. The scan also breaks the em dash between an entry number and its
title. Refusing to mend that mark loses eleven sauces, and the mark never
reaches a record.

## Consequences

### Positive

- A reader sees the whole normalisation in one file of under 40 code lines.
- The wrapper is testable on its own, with no corpus and no extraction.
- Composition is explicit at the assembly root. A reader sees which source is
  normalised and which is not.
- The rules are shared, so a second OCR source cannot drift from the first.

### Negative

- Wrapping costs one list comprehension over the whole body per read.
- One rule set now serves every wrapped source. A source needing different
  handling forces a choice between a parameter and a second wrapper.
- The composition is easy to forget. A new scanned source wired without the
  wrapper fails as a low census rather than as an error.
- `NormalisedText` delegates the witness to the source it wraps, so the front
  matter is read before normalisation runs.

## References

- [ADR-0005: Four layers and no runtime dependencies](0005-hexagon-and-no-runtime-dependencies.md)
- [ADR-0010: Fidelity is a property of the record](0010-fidelity-is-a-property-of-the-record.md)
- [ADR-0013: Normalisation repairs structure, never content](0013-repair-structure-never-content.md)
- [Add a source](../how-to/add-a-source.md)
