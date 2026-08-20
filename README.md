# saucier

Sauce procedures as structured, language-tagged process graphs.

**Status: placeholder.** The name is reserved; the implementation is in
progress. Nothing here is usable yet.

## What this will be

A pipeline that reads culinary source material — starting with public-domain
cookbooks, later demonstration video — and produces a machine-readable
process graph: what must happen, in what order, under what constraints,
independent of who performs it or where.

That graph then projects onto different resource models:

- **`restore`** — the source procedure, one cook, one kitchen.
- **`line`** — a production layout, balanced for takt, validated in simulation.
- **`cell`** — a task specification for robotic execution, plus the kitchen
  designed around it.

Culinary terms are treated as a controlled vocabulary and are never
translated. Terms carry language-independent concept identifiers with
language-tagged surface forms, because *mole* is not "sauce," *recado* is
not "paste," and *nixtamal* is not "corn."

## Licence

MIT for the code. Corpus material is licensed separately and per source; see
`corpus/` once it exists. No corpus is redistributed by this package.
