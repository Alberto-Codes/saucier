# ADR-0018: A mother does not bind to its derivative

## Status

Accepted. Amends ADR-0008's mother-binding clause. ADR-0008 remains accepted.

## Date

2026-09-08

## Context

ADR-0008 binds a mother to the first preparation answering to its name.
Its premise is that the source presents a base before its derivatives.
The lookup checks ordering without checking whether the base survived among the matches.

The 1907 scan names entry 22 `BROWN SAUCE OR ESPAQNOLE`, at line 1730.
No catalogued name exactly matches `espagnole`.
Only `LENTEN ESPAGNOLE`, entry 24 at line 1795, contains that word.
The lookup therefore names a derivative as the mother.

Entry 24 opens with "The ordinary Espagnole being really a neutral sauce in flavour".
The resolver discards that statement as self-reference because the mother lookup returns entry 24 itself.
The tree then prints twelve preparations beneath Lenten Espagnole, including HALF GLAZE and its nine derivatives.

Source order arbitrates only two of ten mother bindings across the two witnesses.
Both are velouté. Espagnole has only one run match in 1907, so ranking cannot explain this failure.

## Decision

**A mother does not bind by a name run to a preparation whose opening paragraph states that mother.**

The statement test remains ADR-0008's whole word run within one sentence of the opening paragraph.
The domain and extraction service share that test through `saucier.domain.statement`.
The guard belongs in `Catalogue.matches`, so parent resolution and tree lookups share the same identity.

An exact catalogued name still wins outright.
For name-run matches, the guard removes candidates on stated evidence.
The remaining matches retain source order. An empty result leaves the mother uncatalogued in that witness.
No score enters parent resolution, consistent with ADR-0012.

ADR-0008 remains accepted. Its subject, shadow, ambiguity, and cycle rules retain their behavior.
Names reaching one preparation still coalesce under the mother concept, so `parent: bechamel` stays `bechamel`.

ADR-0014 says a damaged witness cannot establish absence.
Here, a damaged witness cannot establish identity by promoting a stated derivative when the base's name disappears.
The lookup does not repair `ESPAQNOLE` or infer which preparation the damaged heading names.

## Consequences

### Positive

- The 1907 census changes from 140 / 50 / 90 to 140 / 51 / 89: sauces, derived, unresolved.
- Only 1907 entry 24 changes parent, from `None` to `espagnole`.
- The 1907 Espagnole tree uses the bare concept as its heading. LENTEN ESPAGNOLE becomes a child alongside the existing twelve descendants.
- The Lenten Espagnole tree reports its parent and loses the twelve descendants that belonged to Espagnole.
- The 1909 census remains 151 / 57 / 94. Its JSON and JSONL output remain byte-identical.
- The diff changes from 11 / 19 / 36 to 11 / 18 / 35: unmatched, parent-changed, ocr-suspected.
- All other rendered trees remain identical across both witnesses. Hollandaise retains two children in 1909 and three in 1907.
- The guard preserves all nine correct mother bindings, including eight partial bindings and the exact 1909 Espagnole binding.
- `saucier show espagnole --source escoffier-1907` now reports NOT_FOUND. `show` reads `matches` alone, although `tree` falls back to the declared mother.

### Limits

The guard depends on the witness's opening prose.
The 1907 VELOUTE DE VOLAILLE opening does not state velouté, although the 1909 opening does.
Damage to both a base heading and a derivative's opening can still defeat this guard.

The guard also reads the true base's own opening paragraph.
Eight of the nine surviving bindings are name-run matches, so only the 1909 Espagnole binding escapes this test.
Escoffier opens each of those bases with an ingredient list that does not repeat the sauce's own name.
A base that states its own name loses the heading to the next match in source order.

The guard removes two name-run candidates across both witnesses.
Besides 1907 LENTEN ESPAGNOLE, it removes 1909 VELOUTÉ DE VOLAILLE, which already lost to entry 25 on source order.

An uncatalogued mother is keyed by its concept, not by a heading line.
No entry shares that key, so no entry is held out from stating it.
A damaged heading therefore cannot recognise its own repaired name.
In 1907, entry 22 `BROWN SAUCE OR ESPAQNOLE` does not state Espagnole in its opening paragraph.
The word first appears at line 1755, in the third paragraph.
Had that paragraph opened the entry, entry 22 would record its own identity as its parent.
The cycle check reads heading lines, so it cannot catch a parent that names no entry.

## Alternatives declined

**Exact-name-only mother binding** removes nine bindings, including the incorrect 1907 Espagnole binding.
It also changes eight existing parent values and empties both Hollandaise trees.
That proposal targeted source-order ranking, although the observed failure has only one candidate.
The guard retains every correct binding that exact-name-only lookup would remove.

**Refuse multiple surviving preparations** unbinds velouté in both witnesses.
That loses the tree heading's `derives from pale-roux` statement and overturns ADR-0008's deliberate choice.
The captain declined this stricter variant.

## References

- [ADR-0008: A parent may be any catalogued preparation](0008-a-parent-may-be-any-catalogued-preparation.md)
- [ADR-0012: A resolver may refuse, never rank](0012-a-resolver-may-refuse-never-rank.md)
- [ADR-0014: A damaged witness cannot establish absence](0014-a-damaged-witness-cannot-establish-absence.md)
- Implementation tracker: saucier-lab issue 71
- Superseded issue framing: saucier-lab issue 56
