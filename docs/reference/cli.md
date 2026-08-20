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

Exit codes: `0` on success, `2` when the source is unreadable, matches no
entry pattern, or the catalogue cannot be written.

## `saucier tree CONCEPT`

Prints the derivation tree beneath a concept. Language tags after each title
show the language that title is written in.

```console
$ uv run saucier tree hollandaise
HOLLANDAISE SAUCE  [hollandaise]
├── MALTESE SAUCE  (en)
├── MOUSSELINE SAUCE  (en)
└── NOISETTE SAUCE  (en)
```

The bracket names the concept whose derivations follow, so the heading can
never caption a tree it does not belong to.

Exit codes: `0` on success, `1` when no preparation matches, `2` when the
stored catalogue cannot be read.

## `saucier show CONCEPT [--chars N]`

Prints one preparation. The output carries its title and its source entry and
line. It then lists every term with its language and concept id, the resolved
parent, and the opening of the prose.

`--chars` sets how much prose to print. Default `600`. Prose that was cut
says so, and reports how much was left out.

Lookup accepts the full name or any whole run of words inside it, so
`bordelaise` finds `SAUCE BORDELAISE`. A preparation with alternative names
answers to all of them. `BROWN SAUCE OR ESPAGNOLE` is reachable as either.
When a name matches several preparations, the command prints the best match
and names the others on standard error.

Exit codes: `0` on success, `1` when no preparation matches, `2` when the
stored catalogue cannot be read or the name folds to nothing.
