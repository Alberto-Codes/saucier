# Decisions

Architecture decision records. Each one states a context, a decision, and the
consequences accepted with it. A record is never edited to reflect a change of
mind. It is superseded by a later record.

Decisions about the blog series rather than the code live in a separate
repository, because they govern the writing rather than this implementation.

## Records

- [ADR-0001: The documentation stack](0001-docs-stack.md). Why this site is
  pinned on both sides, and what to watch.
- [ADR-0002: An unresolved parent is recorded as absent, never
  inferred](0002-unresolved-is-not-none.md). Why 95 preparations stay
  unresolved, and why raising that number by guessing fails a test.
- [ADR-0003: Culinary terms carry a language tag and are never
  translated](0003-terms-are-never-translated.md). Why *mole* is not "sauce",
  and what that costs.
- [ADR-0004: Source material is committed, derived output is not
  ](0004-corpus-is-committed-data-is-derived.md). Why a clone runs offline,
  and what may enter the corpus.
- [ADR-0005: Four layers and no runtime
  dependencies](0005-hexagon-and-no-runtime-dependencies.md). What the
  structure buys against what arrives next.
- [ADR-0006: Storage arrives in stages](0006-storage-arrives-in-stages.md).
  Why each store waits for the previous one to fail, and why SQLite rather
  than DuckDB.
- [ADR-0007: The source decides what counts as a
  sauce](0007-the-source-classifies-its-own-contents.md). Why the catalogue
  fell from 166 entries to 124, and why an ambiguous base resolves to nothing.
- [ADR-0008: A parent may be any catalogued
  preparation](0008-a-parent-may-be-any-catalogued-preparation.md). Why
  derived rose from 29 to 50, and which runs of words count as statements.
- [ADR-0009: The source states its own
  identity](0009-the-source-states-its-own-identity.md). Why `escoffier-1907`
  named the wrong edition for two releases, and what replaced the filename.
- [ADR-0010: Fidelity is a property of the
  record](0010-fidelity-is-a-property-of-the-record.md). Why a transcription
  and a scan are not equal evidence, and where that is recorded.
- [ADR-0011: Normalisation is an adapter that wraps a
  source](0011-normalisation-wraps-a-source.md). Where three lines of
  whitespace handling live, and the three places they do not.
- [ADR-0012: A resolver may refuse, never
  rank](0012-a-resolver-may-refuse-never-rank.md). Why the unresolved count
  is an instrument, and what a model layer may not do to it.
