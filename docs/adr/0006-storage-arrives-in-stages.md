# ADR-0006: Storage arrives in stages, and each stage answers a named failure

## Status

Accepted. Moved here from the series repository, which is private. This
decision governs code, so it belongs beside the code.

## Date

2026-08-19

## Context

The eventual system uses Postgres, Kafka, Redis, and object storage. Presented
together that reads as over-engineering, and the recurring objection is fair.
Nothing in the current implementation needs any of it.

The objection is answered by ordering rather than by argument. A component that
arrives before the reader has felt its absence is unjustified, whatever the
diagram says.

The access pattern also matters. This corpus is parsed once and then queried
repeatedly. That is analytical work, not transactional work, which changes
which store is correct at each stage.

## Decision

**Each store arrives only after the previous one visibly fails.**

| Stage | Arrives when | Why that one |
| --- | --- | --- |
| JSON files | Now | Inspectable by eye, which is the point while a human still verifies the parser |
| JSONL | Appending one record means rewriting the file | Streamable and appendable, still plain text |
| SQLite | Queries are needed, and results written back | `sqlite3` is in the standard library, so no runtime dependency appears. WAL mode gives many readers with one writer |
| Object storage | Video arrives | Blobs do not belong in a database, and distributed workers need shared access |
| Postgres | Concurrent writers appear | Durability and transactional integrity for a work ledger |

*Amended by [ADR-0016](0016-jsonl-is-the-interchange-not-a-store.md).* The
JSONL row predicted a break that never came. The store writes one file per
witness, so a second witness rewrote nothing. JSONL arrives as the
interchange between extraction and every later store, not as a store of its
own. The JSON snapshot stays the working store, and SQLite is the next rung.

**SQLite is the entry point rather than DuckDB.** DuckDB permits one
read-write process or several read-only ones against a file, with no
cross-process writer concurrency. A worker pool, which this system acquires by
design, meets lock contention rather than throughput.

The deciding argument is the destination. SQLite to Postgres is a connection
string under SQLModel, and the storage code survives. DuckDB to Postgres is a
rewrite.

**DuckDB still has a place, alongside the store rather than as it.** It reads
JSONL and Parquet in place with no load step, which suits ad hoc aggregation.
Nothing may depend on it holding state.

## Consequences

### Positive

- Every component is introduced after a failure the reader has already seen, so
  the architecture is demonstrated rather than asserted.
- The current stage costs no runtime dependency, which keeps ADR-0005 intact.
- The migration path preserves the storage code rather than replacing it.

### Negative

- Early stages are knowingly inadequate, and someone will find JSON at a point
  where JSONL would already be better.
- The staged path means writing a migration more than once.
- DuckDB will be proposed again, because it is a good fit for the query
  workload considered on its own.

## References

- [ADR-0005: Four layers and no runtime dependencies](0005-hexagon-and-no-runtime-dependencies.md)
