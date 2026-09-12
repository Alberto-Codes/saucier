# ADR-0020: A claim is a record

## Status

Accepted. ADR-0016 remains accepted. Its section "What version one stops
before" defers claim records to a later record that changes the domain.
This is that record. No code lands with it.

## Date

2026-09-12

## Context

The catalogue stores one value where the domain holds a claim.
`Preparation.parent` is one nullable concept id
(`src/saucier/domain/models.py:160`). Nothing on the record says who read
the text, from which words, or whether the reader refused. Each release
since v0.1.0 added a property to that value or changed the rule that
writes it. None added a second kind of record. The investigation report
of 2026-09-12 traces this in its sections 2 and 4.

The same deficiency produced every recent per-record question. The
captain calls those questions the canary in the coal mine. Four of them
are measured here at `434f919`.

**The evidence is computed and discarded.** `Span` at
`src/saucier/domain/statement.py:42` is where a name was stated. The
resolver computes it for every candidate (`statement.py:64-80`), keeps
the names it reached, discards the spans, and returns one concept id
(`src/saucier/services/extraction.py:460-461`).
`saucier show` then recomputes the stated candidates from the body at
display time (`src/saucier/adapters/driving/cli.py:452-454`), because the
record does not carry them.

**Two states stand where the text has three.** An unresolved parent
is `None` whether the opening paragraph states no candidate or states
several. ADR-0002 spent a whole record establishing that the second
reading exists, because the field cannot say which one applies. The split
is measurable and the record hides it:

```console
$ uv run python -c "
from saucier.infrastructure.bootstrap import escoffier_sources
from saucier.services.extraction import extract, parent_candidates, stated_candidates, own_names
for s in escoffier_sources():
    c = extract(s); k = parent_candidates(c)
    n = [len(stated_candidates(p.body, own_names(p), k)) for p in c.preparations if p.parent is None]
    print(c.source_id, 'none', n.count(0), 'several', sum(x > 1 for x in n))"
escoffier-1909 none 78 several 16
escoffier-1907 none 82 several 7
```

**One folded string does four jobs.** A `Term.concept` is folded from the
surface form (`models.py:75`). The same string is the mention in a
heading, the identity `parent` points at, the key `by_concept` indexes
(`models.py:256-271`), and the resolution `_recorded` writes
(`extraction.py:422-435`). Lab issue 60 names the cost: a resolution
decision becomes identity and cannot later abstain.

**The scan spells a mother's name `ESPAQNOLE`.** The 1907 witness declares
the mother at line 877 and names entry 22 at line 1730:

```console
$ sed -n '877,878p' corpus/escoffier-1907.txt
7.  The  basic  sauces :  Espagnole,-  Veloute,  Bechamel,
Tomato,  and  Hollandaise.
$ sed -n '1730p' corpus/escoffier-1907.txt
22— BROWN  SAUCE  OR  ESPAQNOLE
$ uv run python -c "from saucier.domain.types import to_concept_id as f; print(f('ESPAQNOLE'), f('Espagnole'))"
espaqnole espagnole
```

The declaration folds to `espagnole`. The heading folds to `espaqnole`.
Folding resolves orthography and not damage, and ADR-0013 forbids the
repair. So the mother has no bound record in that witness, and two
commands answer differently:

```console
$ uv run saucier show espagnole --source escoffier-1907
no preparation named 'espagnole'
exit=1
$ uv run saucier tree espagnole --source escoffier-1907 | head -2
espagnole  [espagnole]
├── HALF GLAZE  (en)
exit=0
```

Both are correct under ADR-0018. `tree` falls back to the declared mother
(`cli.py:348`) and `show` reads `matches` alone (`cli.py:412-415`). The
asymmetry exists because the mother's identity and the record's address
are one lookup rather than two facts.

The investigation report put two framings to the captain. Framing A makes
`parent` a projection of claims on day one and re-emits every reading of
the parser as a claim. Framing B adds a claim record beside the untouched
value. The captain chose A on 2026-09-12 and called it a growth spurt.
This record is the design that choice needs.

It comes before the code for one reason. Lab issue 60 asks for the four
identities to be settled before the interchange makes today's ids
permanent. ADR-0016 already requires a new schema version for any new
field. The version that first carries a claim fixes its ids for every
later reader, so the ids are decided here and the version is not.

## Decision

**A claim is a record of the interchange. `Preparation.parent` is a
projection of the parser's current asserted `derives-from` claim, or
unresolved where the parser abstained. No code writes the value on its
own.**

### The record

A claim record carries the envelope of ADR-0016 and seven fields.

| Field | Holds |
| --- | --- |
| `schema` | The version the change that emits the first claim assigns. Not `saucier/1`, whose reader rejects the type (ADR-0016). |
| `type` | `claim` |
| `id` | Derived from every field below except `evidence.run`. Recomputed on the way back. |
| `catalogue` | The catalogue id of the witness the claim was read from, as a preparation record names its catalogue (ADR-0016). |
| `subject` | A record address, or a concept id. |
| `predicate` | `derives-from`, `names`, or `binds-mother`. |
| `object` | A concept id or a record address. `null` when the status is not `asserted`. |
| `status` | `asserted` or `abstained`. |
| `recorder` | Who read the text. `hand` for a person. A rule names itself. |
| `evidence` | Zero or more statements, in the order the text carries them. |

Lab issue 59 drafted ten fields and said not to require one until a
present use case earns it. Section 5.3 of the investigation report lists
the use cases. Each field was tested against them.

**`catalogue` names the witness.** A `binds-mother` subject is a concept
id, and both witnesses declare the same five mothers. Without the field,
one claim cannot be told from the other. ADR-0016 already writes the field
on a preparation record, so the claim record writes it the same way. Two
witnesses that abstain on one mother then differ in this field, so their
claims differ in id. When `subject` or `object` is a record address, the
catalogue id inside that address must equal the `catalogue` field. The
reader rejects a claim where the two disagree, as ADR-0016 rejects a
preparation whose catalogue the stream never carries.

**`object` stays and `value` goes.** Every object a symptom needs is an id.
A parent is a concept id. A name reaches a concept id. A mother binds to a
record address. No claim in this catalogue carries a literal, so no field
holds one.

**`evidence` is inline, not a list of ids.** A statement has no identity
apart from where it sits, which lab issue 60 requires of a mention. A
separate evidence record would need an id of its own, and the only stable
id it could carry is its address. So the address is written on the claim.

**`recorder` replaces `generated_by`.** The glossary already names who
recorded a thing: `hand` in this release, and a rule reader or a model
names itself. One concept takes one term. The value for the parser is the
name of the rule that read the text, as `RecordedProcedures` already names
its recorder.

**`valid_time` goes.** The time a statement holds is the edition, and the
witness of the record the evidence anchors to carries the edition. No
symptom needs a second one.

**`recorded_time` goes.** ADR-0016 writes no timestamp, because a
timestamp changes the bytes without adding evidence. Framing A re-emits
every reading of the parser as a claim, so a time on each would make every
export differ from the last one. The time a claim was recorded belongs to
the activity that produced it, which is lab issue 60's activity id and
later work.

**Two statuses are written and one is read.** Lab issue 59 names five
states: asserted, abstained, contradicted, superseded, retracted. The
record writes `asserted` and `abstained`. The interchange does not mutate,
and lab issue 59 makes correction append-only, so no line can be rewritten
to say it was contradicted. That state is read off the stream. In this
release every claim in the stream is current, because nothing supersedes.

**Retraction and supersession wait for a writer.** No recorder in this
release appends. The parser re-emits every claim on every run, and `data/`
is not tracked, so there is nothing to supersede. The record therefore
drops `supersedes` and `retracted`, for the reason it drops `value`,
`valid_time`, and `recorded_time`. The change that gives them a writer
admits them.

**Cardinality decides what contradiction means.** A predicate is
single-valued or many-valued, and the rule reads only the single-valued
ones. `derives-from` is one per preparation. `binds-mother` is one per
mother per witness. `names` is many per record, because `by_concept` is a
projection of `names` claims. A single-valued claim is contradicted when a
current asserted claim shares its catalogue, its subject, and its
predicate, and differs in object. Two `names` claims on one record never
contradict.

### The predicates

This record names three predicates. A later record that emits a fourth
names it.

**`derives-from`.** The subject is a record address and the object is a
concept id. The parser records exactly one per preparation. It is
asserted when the opening paragraph states one candidate, with every span
of that candidate. It is abstained when the paragraph states none or
several, with every span of every candidate, in the order stated. Those
candidates are what `saucier show` prints as `stated` today. The object is
the value `_recorded` writes now, so the projection below is an identity.

**`names`.** The subject is a record address and the object is a concept
id. The heading reader records one per term `terms_in` yields, with the
term's span in the heading as evidence. `by_concept` becomes a projection
of these claims. The heading at 1909 line 674 shows why that matters:

```console
$ sed -n '674p' corpus/escoffier-1909.txt
1—ORDINARY OR WHITE CONSOMMÉ
$ uv run python -c "from saucier.services.extraction import terms_in; print([(t.surface, t.concept) for t in terms_in('ORDINARY OR WHITE CONSOMMÉ')])"
[('ORDINARY', 'ordinary'), ('WHITE CONSOMMÉ', 'white-consomme')]
```

That entry sits in chapter I and is outside the catalogue today
(ADR-0015). When an entry like it enters, its doubtful name is a `names`
claim with the heading as evidence. The claim carries the span, so a
reader checks the doubtful name against the heading. The parser needs no
special case.

**`binds-mother`.** The subject is a concept id the source declares as a
mother, and the object is a record address. The parser records one per
mother per witness. It is asserted with the heading span of the name that
bound under ADR-0018, and abstained with no evidence when no name
survives. The `catalogue` field names the witness. A claim on `bechamel`
in one witness is not a claim on `bechamel` in the other. The claim whose
`catalogue` is `escoffier-1907` and whose subject is `espagnole` is an
abstention. `show` and `tree` both read that one claim, so the asymmetry
above has no second lookup to come from.

### The evidence

**The evidence of a claim is zero or more statements, and a statement
reuses `Span` unchanged.** A statement is three things. The first is the
address of the record whose text carries it. The second is which text of
that record, `heading` or `opening`. The third is the triple
`saucier.domain.statement` declares at line 42.
The triple is a segment index, a first word, and one past the last,
over the folded segments of that text. That is what the resolver computes
today, so re-emitting the parser's readings emits exactly what the
resolver saw.

A fourth element, `run`, is the folded words the span covers. It is
derived, written for a reader who opens the corpus by hand, and
recomputed on the way back under ADR-0016's rule for derived fields. The
reader rejects a statement whose span lies outside the text's folded
segments or whose run is not what the span covers.

Two worked examples, measured at `434f919`:

| Claim | Status | Evidence |
| --- | --- | --- |
| `escoffier-1909:line:1449` derives-from `espagnole` | asserted | opening (0, 11, 12), (1, 2, 3), (2, 20, 21) `espagnole` |
| `escoffier-1909:line:2192` derives-from | abstained | opening (0, 4, 5) `bechamel`, opening (2, 3, 5) `lobster butter` |

The first is `LENTEN ESPAGNOLE`, whose opening states the mother three
times, so the claim carries three spans. The second is `CARDINAL SAUCE`,
which ADR-0015 left unresolved because it states a base and a finish.
Under this record the abstention carries both spans, and nothing
recomputes them.

```console
$ uv run python -c "
from saucier.infrastructure.bootstrap import escoffier_sources
from saucier.services.extraction import extract, parent_candidates, stated_candidates, own_names
from saucier.domain.statement import folded_segments, spans_in
c = extract(next(iter(escoffier_sources()))); k = parent_candidates(c)
for p in c.preparations:
    if p.ref.line in (1449, 2192):
        st = stated_candidates(p.body, own_names(p), k)
        print(p.ref.line, p.title, p.parent, {s: spans_in(s.split('-'), folded_segments(p.body)) for s in st})"
1449 LENTEN ESPAGNOLE espagnole {'espagnole': ((0, 11, 12), (1, 2, 3), (2, 20, 21))}
2192 CARDINAL SAUCE None {'bechamel': ((0, 4, 5),), 'lobster-butter': ((2, 3, 5),)}
```

A span is measured in folded words, so it is exact only for the text it
was measured over. The fidelity of a statement is the fidelity of its
record (ADR-0010). A box on a page image (lab issue 36) is a different
kind of evidence, and a later record names it.

### The identities

**Four identities, each with its own id.** A record address, a concept
id, a statement address, and a claim id. None of them is another one
spelled differently.

- A record address is `escoffier-1909:line:1392`, as ADR-0016 defines it.
  It says where a reader opens the text. It is not a resolution.
- A concept id is `espagnole`, as ADR-0003 defines it. What lab issue 60
  calls an entity id is a concept id in this vocabulary, and the glossary
  forbids "entity" as a synonym.
- A statement address is a record address, a text, and a span. A mention
  has no id apart from where it sits.
- A claim id is derived from the claim, as the next rule states.

**Ids are deterministic. No id is opaque.** Four pieces of evidence settle
this, and none points the other way.

1. ADR-0016 decides "no opaque identifiers, because every record already
   has an address a reader can open." A claim record joins that
   interchange.
2. ADR-0016 requires that identical catalogues produce identical bytes.
   An id minted at parse time changes the bytes without adding evidence,
   which is the exact reason ADR-0016 gives for writing no timestamp.
3. `data/` is not tracked and is reproduced by `saucier parse` (ADR-0004).
   An opaque id needs a place to survive between runs. That place is a
   store, and no store arrives with this record.
4. ADR-0016 verifies every derived field on the way back. A derived id can
   be recomputed and checked. An opaque id cannot.

Lab issue 60 warns that a content hash detects mutation and is not
semantic identity, and that renaming a term must not rename the entity.
That warning governs the concept id, and the next rule answers it. It
does not argue for an opaque claim id. Correcting a span creates a new
claim with a new id, which lab issue 60 also allows.

**A claim id is the SHA-256 of its fields.** The input is `catalogue`,
`subject`, `predicate`, `object`, `status`, `recorder`, and `evidence`
without `run`, in that key order, with no whitespace, as UTF-8. The id is
the hex digest with the prefix `sha256:`, so the function is named in the
id. Two claims with the same input are one claim, and the reader rejects
the second line as a repeated id, which ADR-0016 already does. Two
witnesses that abstain on one mother differ in `catalogue`, so their ids
differ.

**The identity a mother's claims point at is its concept id, as the source
declares it. It is not a new key.** Three measurements settle this.

1. Both witnesses declare the same five mothers, and each declaration
   folds to the same five ids:

    ```console
    $ uv run saucier parse | grep mothers
                    mothers: bechamel, espagnole, hollandaise, tomato, veloute
                    mothers: bechamel, espagnole, hollandaise, tomato, veloute
    ```

2. Every recorded parent already holds one of two things. It holds a
   declared mother's concept id, or it holds the concept id of the
   preparation it reaches. Nothing else occurs:

    ```console
    $ uv run python -c "
    from saucier.infrastructure.bootstrap import escoffier_sources
    from saucier.services.extraction import extract
    for s in escoffier_sources():
        c = extract(s)
        off = [(p.parent, c.find(p.parent)) for p in c.preparations if p.parent and (c.find(p.parent) is None or c.find(p.parent).concept != p.parent)]
        print(c.source_id, len(off), sorted({v for v, _ in off}), 'unbound', sum(f is None for _, f in off))"
    escoffier-1909 22 ['bechamel', 'espagnole', 'hollandaise', 'tomato', 'veloute'] unbound 0
    escoffier-1907 17 ['bechamel', 'espagnole', 'hollandaise', 'tomato', 'veloute'] unbound 4
    ```

    Every parent whose value differs from the concept of the record it
    reaches is a declared mother. The four that reach no record are all
    `espagnole` in the scan. So the object of a `derives-from` claim is
    already an identity and never a stated name. A new key would rename
    every recorded parent to say what it says now.

3. A new key needs a table from key to name. That table is a store, which
   ADR-0006 stages later and this record does not build.

The 1907 case then reads as follows. The heading reader records that line
1730 names `espaqnole`, which is true of the scan. The parser records an
abstention for `binds-mother espagnole` in the catalogue
`escoffier-1907`, because no name survives. `show` and `tree` have the
same two claims to read: the declaration and the abstention. A later
recorder can bind the two with a claim of its own. The evidence may be the
page image (lab issue 36), or an alignment of the kind the diff already
labels for other headings. Nothing repairs the name, and ADR-0013 stands.

A concept id is language-bound. A witness in another language declares
the mother under another name, and folding does not cross languages. That
is an alignment claim between two concept ids. Lab issue 43 leaves the
mechanism open, and section 6 of the investigation report leaves it to
later work.

### The projection

**`parent` is the object of the parser's current asserted `derives-from`
claim on the record, and `None` otherwise.** The parser records one
`derives-from` claim per preparation, so a preparation is resolved when
that claim is asserted and unresolved when it is abstained. ADR-0002
stands. `None` means the parser abstained, and it never means the
preparation has no parent.

The change that lands this record measures the census before and after
the re-emission. This record predicts nothing about that measurement.

### What this record does not decide

- **No code.** No module under `src/` changes. `saucier/1` is unchanged,
  and today's reader rejects a claim line. The change that emits the first
  claim assigns the next schema version, as ADR-0016 requires.
- **No store.** SQLite projects the stream later (ADR-0006, lab issue 62).
  Delete it, replay, obtain the same answers, claims included.
- **No re-emission now.** The parser's readings become claims in the
  change that lands the record.
- **Not the census.** The captain has not decided it. This record changes
  the shape the census rests on and no number in it.
- **Not the second recorder.** A hand claim or a model claim may one day
  disagree with the parser. Which claim the projection then reads, and
  whether such a claim may replace a parser abstention, decides the
  census. ADR-0012 says a model may not clear an abstention. This record
  adds no rule to that, and the first claim by a recorder other than the
  parser waits for one.
- **Not retraction or supersession.** `supersedes` and `retracted` have no
  writer in this release, so the record defers both. The change that gives
  them a writer admits them, once a present use case earns the field.
- **Not the activity.** Who ran what and when is lab issue 60's activity
  id, and a confidence is metadata on that activity (lab issue 59).
- **Not procedures.** ADR-0017's procedures stay as they are. An operation
  as a claim is later work.
- **Not the naming rule.** This record decides that evidence is a field of
  the claim record and what that field holds. The naming rule for domain
  vocabulary, recorded in its own change, decides when a term such as
  statement earns a named function.
- **Not the glossary text.** The glossary describes what the code holds.
  The change that lands the record adds `claim`, `evidence`, `run`, and the
  three predicates, and extends `record` and `recorder`. That change also
  resolves two collisions this record creates. The glossary defines Subject
  as what an entry's own name denotes, and `subject` here is the subject of
  a triple. The glossary scopes Statement to the opening paragraph, and a
  statement here is any evidence address, including a heading span. This
  record decides neither entry.

## Consequences

### Positive

- One string stops doing four jobs. `by_concept` projects `names` claims,
  `matches` projects `binds-mother` claims, and `parent` projects
  `derives-from` claims.
- An abstention has a shape. None stated and several stated are two
  records, not one `null`, and nothing recomputes the candidates at
  display time.
- `show` and `tree` read one set of claims, so the 1907 Espagnole cannot
  answer differently in the two.
- A reading by hand has a record type. ADR-0002 asked that a later stage
  record what filled the value and from what evidence. The record does
  that and prose does not.
- A proposal by a model is a claim with a recorder. ADR-0012 stands: it
  never writes `parent`.
- A sentence about the corpus in a later record can point at a claim id
  and a span. A test then reads the span, which is lab issue 61's first
  question.
- Ids are derived, so two runs export identical bytes and the reader
  verifies every id.

### Negative

- This is the larger change. A schema version, a re-emission of every
  reading, a second record type in the domain, and every construction
  site that states `parent` today. Byte-identical exports across the
  boundary are not possible.
- A claim id is checked by a tool and not by eye. A reader sees 64 hex
  characters where ADR-0016 promised an address. The evidence beside it
  is the address.
- One of five states is read off the stream, so one line cannot say
  whether its claim is contradicted.
- Two of five states have no writer, so a claim cannot yet be retracted or
  replaced. A recorder that appends waits for the change that admits them.
- A concept id as identity is language-bound, and a cross-language mother
  waits for an alignment claim.
- The first claim by a recorder other than the parser cannot land until
  the second-recorder rule is decided, because that rule moves the census.
- The glossary lags the decision until the code lands.
- A span is measured in folded words over one text. A change to the fold
  or the segmenter moves every span, and the reader will reject the old
  ones. That is the correct failure and it is a loud one.

## References

- [ADR-0002: An unresolved parent is recorded as absent, never inferred](0002-unresolved-is-not-none.md)
- [ADR-0003: Culinary terms carry a language tag and are never translated](0003-terms-are-never-translated.md)
- [ADR-0004: Source material is committed, derived output is not](0004-corpus-is-committed-data-is-derived.md)
- [ADR-0006: Storage arrives in stages](0006-storage-arrives-in-stages.md)
- [ADR-0010: Fidelity is a property of the record](0010-fidelity-is-a-property-of-the-record.md)
- [ADR-0012: A resolver may refuse, never rank](0012-a-resolver-may-refuse-never-rank.md)
- [ADR-0013: Normalisation repairs structure, never content](0013-repair-structure-never-content.md)
- [ADR-0015: The chapter decides](0015-the-chapter-decides.md)
- [ADR-0016: JSONL is the interchange, not a store](0016-jsonl-is-the-interchange-not-a-store.md)
- [ADR-0017: A procedure quotes its witness](0017-a-procedure-quotes-its-witness.md)
- [ADR-0018: A mother does not bind to its derivative](0018-a-mother-does-not-bind-to-its-derivative.md)
- [Data model](../reference/data-model.md)
- [Glossary](../reference/glossary.md)
- Investigation report "Saucier: the traced evolution, the shared
  deficiency, and the next tech-stack step", 2026-09-12, sections 3 to 6
- saucier-lab issues 13, 36, 38, 43, 59, 60, 61, 62
