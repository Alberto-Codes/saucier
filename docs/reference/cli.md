# Command line reference

The `saucier` command has no runtime dependencies. It is built on `argparse`.

## `saucier parse`

Reads the committed source, extracts the catalogue, writes it to
`data/<source-id>.json`, and reports a summary.

| Line | Meaning |
| --- | --- |
| `source` | Identifier of the source that was read |
| `mothers` | Base preparations, as named by the source itself |
| `sauces` | Preparations that qualified as sauces |
| `derived` | Preparations linked to a base |
| `unresolved` | Preparations whose prose names no mother |

Exit codes: `0` on success, `2` when the source is unreadable or matches no
entry pattern.

## `saucier tree CONCEPT`

Prints the derivation tree beneath a concept. Language tags after each title
show the language that title is written in.

```console
$ uv run saucier tree hollandaise
```

Exit codes: `0` on success, `1` when no preparation matches.

## `saucier show CONCEPT [--chars N]`

Prints one preparation. The output carries its title and its source entry and
line. It then lists every term with its language and concept id, the resolved
parent, and the opening of the prose.

`--chars` sets how much prose to print. Default `600`.

Lookup accepts the full name or its ending, so `bordelaise` finds
`SAUCE BORDELAISE`. A preparation with alternative names answers to all of
them. `BROWN SAUCE OR ESPAGNOLE` is reachable as either.

Exit codes: `0` on success, `1` when no preparation matches.
