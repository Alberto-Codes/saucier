# ADR-0016: JSONL is the interchange, not a store

## Status

Accepted. Amends the JSONL row of
[ADR-0006](0006-storage-arrives-in-stages.md).

## Date

2026-09-03

## Context

ADR-0006 stages the stores and names the failure each one answers. Its JSONL
row reads: arrives when appending one record means rewriting the file.

That break never came. `JsonCatalogueStore` writes one file per witness. The
1907 witness arrived in v0.3.0 and rewrote nothing of the 1909 file. Two
witnesses are two snapshots, and nobody appends inside a witness. Within a
witness the whole file is rewritten, and that is a cost, not a break. The
same release paid two other costs. The source id rename rewrote every 1909
record to change one field. `saucier diff` loads two whole files to compare
anything. Neither is an append, and JSONL answers neither. The first is
history, and the second is a query.

The break the JSON snapshot does show is a different one. The two files are
complete object snapshots, and the only way to consume one preparation is to
learn the nested `Catalogue` document first. A SQLite loader, an analytical
scan, or a graph projection has to reproduce the Python object model first.
So does a second implementation in another language.
The project has one reusable boundary, and it is a set of dataclasses.

Every later store on the ladder is a projection of the same records. The
ladder needs a representation those projections can share and that none of
them owns.

## Decision

**A serialization and a database are different decisions.** JSONL is the
interchange. It carries catalogues out of this process and into any other,
one record per line, and it claims nothing else. It does not index, it does
not mutate, it does not keep history, and it does not walk a graph. SQLite
earns those jobs when a named operation needs one of them.

**The JSON snapshot stays the working store.** `JsonCatalogueStore` still
backs `parse`, `show`, `tree`, and `diff`. The interchange is a second
representation beside it, not a replacement. A v0.4.0 `data/` directory
works unchanged.

**Two commands prove the round trip.** `saucier export` writes every stored
catalogue to standard output as JSONL and writes nothing else there. `saucier
import --check` reads JSONL from standard input, rebuilds every catalogue in
memory, and prints the census. The flag is mandatory in this release, so the
verb cannot imply a write the command does not perform. A stream that
carries no catalogue fails the check. Without `pipefail` a pipeline returns
the last command's status, and an empty stream is what a failed export
leaves behind.

**The codec is a driven adapter behind a port of its own.** `CatalogueStore`
describes a place. The interchange is a representation, so
`CatalogueInterchange` describes it separately, with `encode` and `decode`.
The domain does not change. JSON syntax stays outside the hexagon.

### The record

Every record carries an envelope of three fields: `schema`, `type`, and `id`.
The schema is `saucier/1`. There are two record types.

A catalogue record carries the catalogue apart from its preparations. That
is the witness fields, which are the work, the edition as the front matter
states it, the origin, and the fidelity. Then the sorted mothers, how many
preparations follow, and `entries_read`. Its id is the catalogue's source
id. The count is what lets the reader refuse a stream cut at a line
boundary, because such a stream is otherwise complete JSON.

```json
{"schema":"saucier/1","type":"catalogue","id":"escoffier-1909","work":"escoffier","edition":{"statement":"New and Revised Edition, January 1909","stated_year":1909,"impression":"January 1920","copyright_year":1907},"origin":"Project Gutenberg 71395","fidelity":"transcription","mothers":["bechamel","espagnole","hollandaise","tomato","veloute"],"preparations":151,"entries_read":2963}
```

A preparation record names its catalogue and carries the title, the terms
with their language tags, the concept, the parent, the reference, and the
body. Its id is the catalogue id and the heading line, joined.

```json
{"schema":"saucier/1","type":"preparation","id":"escoffier-1909:line:38713","catalogue":"escoffier-1909","title":"STRAWBERRY SAUCE","terms":[{"surface":"STRAWBERRY SAUCE","language":"en","concept":"strawberry-sauce"}],"concept":"strawberry-sauce","parent":null,"ref":{"entry":2417,"line":38713,"fidelity":"transcription"},"body":"Proceed as for No. 2416."}
```

Six rules govern the record.

**An id is a source-local address, never a resolution.** A preparation id
derives from the catalogue id and the heading line. It says where a reader
can check the claim. It does not say that two catalogues hold the same
sauce. The entry number is not identity, because the scan repeats numbers. The
domain does not forbid two preparations on one line, so the writer
refuses such a catalogue rather than emit a stream its reader rejects.
Lab issue #60 separates record, entity, mention, and claim identity, and
none of that arrives here.

**A catalogue id is a source id, not a witness id.** `Witness.source_id` is
the work and the edition year. A second scan or a second transcription of
one edition would share it. Their preparation ids would collide wherever a
heading line coincides. The record carries the witness
fields, and that does not make its id a witness id. So version one carries
one catalogue per source id, and the reader rejects a second as a
duplicate. Collating two texts of one printing needs the identity work in
lab issue #60 and a later schema version. This record makes no claim that
the current identifiers support it.

**A `null` parent means unresolved.** It never means the preparation has no
parent. ADR-0002 governs the interchange as it governs the domain.

**Surface forms survive as written.** The writer emits UTF-8 with no ASCII
escaping, so `VELOUTÉ` is six characters on disk. Every term keeps its
language tag. The two commands set UTF-8 on their own streams rather than
trusting the locale, because the stream is UTF-8 by contract.

**Derived fields are written for the reader and verified on the way back.**
A catalogue record carries its id, and a preparation record carries its
concept. Both derive from other fields. The reader recomputes each one and
rejects a record where the two disagree.

**Identical catalogues produce identical bytes.** The writer emits catalogue
records first, in the order given, then each catalogue's preparations in
source order. Keys are emitted in one fixed order, with no whitespace, and
every line ends in one newline. No timestamp appears, because a timestamp
changes the bytes without adding evidence.

### The reader

The reader consumes one line at a time, as UTF-8, and never reads the
stream whole. It rejects, with the line number, any of the following:

- a line that is not UTF-8, or not one JSON object,
- an object that repeats a key, because `json` would keep the last value
  and say nothing,
- a catalogue that receives a different number of preparations than its
  record states,
- a schema other than `saucier/1`,
- a type other than `catalogue` or `preparation`,
- a missing or blank id, or an id seen on an earlier line,
- a field the schema does not name, or a named field that is absent,
- a value of the wrong type, including a blank parent,
- a derived field that disagrees with what it derives from,
- a preparation whose catalogue the stream never carries,
- a preparation that cites another fidelity than its catalogue,
- any rebuilt catalogue the domain refuses.

Records may arrive in any order, and a preparation may precede the
catalogue record it names. The reader rebuilds catalogues in the order
their catalogue records arrived, and each catalogue's preparations in the
order their records arrived. The writer emits them in the catalogue's own
order, so what was written reads back equal. The reader does not sort by
line, because the domain admits a catalogue whose lines do not ascend, and
sorting would rebuild a different one. Two complete exports cannot be joined,
because `saucier export` writes every configured catalogue and the second
copy repeats every id. The reader rejects the first repeat. The reader
holds the preparations it has read until the stream ends. A catalogue is
validated whole, and the domain holds every preparation in one tuple. What
streams is the text. A consumer that wants one preparation at a time reads
records and does not rebuild the catalogue.

### What version one stops before

No claim records. `Preparation.parent` is one field, and it stays one field
until lab issue #59 changes the domain. No entity, activity, evidence, or
agent records, which lab issue #58 owns. No JSON-LD keywords. The ids are
stable strings and the records are typed, so a JSON-LD context can be laid
over them later without rewriting a byte. No difference rows, because the
domain does not own them. No opaque identifiers, because every record already
has an address a reader can open.

## Consequences

### Positive

- One command emits a stream that a shell, DuckDB, or a loader in another
  language reads with no import of this package.
- The reader is strict, so a hand-edited stream that lies about a concept or
  a catalogue is reported at its line rather than loaded. So is one that
  repeats a key, or one that was cut after its catalogue records.
- An empty stream fails `import --check`, so a pipeline whose export failed
  cannot end in a zero.
- A later SQLite projection consumes this stream and never imports
  extraction. Delete the database, replay the stream, and obtain the same
  answers.
- The JSON snapshot is untouched, so no published tag is stranded.

### Negative

- ADR-0006's JSONL row predicted a break that never arrived, and this record
  says so. The table stays as written, with a note pointing here.
- The same preparation is rendered by two adapters in two shapes. The two
  formats have two jobs and are expected to diverge, but for now each
  renders the witness and the edition on its own.
- The reader checks the form of a parent and not its referent. A parent
  that names nothing in its catalogue is carried as written. The domain
  permits it, and the reader adds no rule the domain does not hold.
  `tree` will never show such a preparation under a root.
- `export` reads the corpus as well as the store. The configured witnesses
  supply the ids, and each witness reads its id from its front matter. A
  store that could list what it holds is a later port change.
- A catalogue id names an edition, not a text of it. Two scans of one
  printing would collide on every id, so this schema carries one catalogue
  per source id. Lifting that limit needs the identity in lab issue #60 and
  a new schema version, and this release does not claim to support
  collation.
- Two complete exports cannot be joined. Each carries every configured
  catalogue, and an export that selects one is a later feature.
- Rebuilding a catalogue holds every preparation of that catalogue in memory.
  That is the domain's shape, not a limit of the format, and this record
  does not hide it behind the word stream.
- `import` performs no import. The mandatory flag makes that visible at the
  cost of a verb that promises more than the command does.
- A field added to the schema needs a new schema version, because the reader
  rejects unknown fields. The alternative is a reader that silently ignores
  what it does not understand, and this project does not guess.

## References

- [ADR-0002: An unresolved parent is recorded as absent, never inferred](0002-unresolved-is-not-none.md)
- [ADR-0005: Four layers and no runtime dependencies](0005-hexagon-and-no-runtime-dependencies.md)
- [ADR-0006: Storage arrives in stages](0006-storage-arrives-in-stages.md)
- [ADR-0010: Fidelity is a property of the record](0010-fidelity-is-a-property-of-the-record.md)
- [Glossary](../reference/glossary.md)
