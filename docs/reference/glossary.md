# Glossary

One term per concept, one concept per term. These are the project's canonical
nouns. Docs, code identifiers, commit messages, and conversation use these
words and no synonyms for them. Coin a new term only with a new glossary entry
in the same change.

## What a source yields

**Source**
:   One document the extractor reads, identified by a `source_id` such as
    `escoffier-1907`. Not "book", "text", or "file".

**Corpus**
:   The tracked collection of source material under `corpus/`. One corpus
    holds many sources. Not "dataset" or "data".

**Entry**
:   A numbered division of a source, in the source's own numbering. Escoffier
    numbers 3,094 of them. Not "section" or "record".

**Preparation**
:   One entry that describes something to make. The unit this project
    extracts. Not "recipe", which is a consumer-facing document Escoffier
    does not write. Not "dish", which is what a preparation is served on.

**Catalogue**
:   Every preparation read from one source, plus the mothers that source
    names. Not "database", "index", or "collection".

## Terms and concepts

**Term**
:   One surface form in one language, with the language tagged. Not "name",
    "label", or "string".

**Surface form**
:   A term exactly as the source writes it. Never translated, never
    normalised beyond folding for identity. Not "spelling" or "variant".

**Concept**
:   The language-independent identity a term denotes, carried as a
    `ConceptId`. `espagnole` and `salsa española` are two terms and one
    concept. Not "entity", "node", or "key".

**Folding**
:   Reducing a surface form to a concept id by stripping diacritics, case,
    and punctuation. Resolves orthographic variation only. Not "normalising"
    (too broad) and not "matching" (folding decides nothing about meaning).

**Gloss**
:   An English rendering of a term, recorded beside it and never in place of
    it. A gloss is not a term and never substitutes for one.

## Derivation

**Mother**
:   A preparation the source itself names as foundational. Escoffier names
    five. Not "base sauce" in prose (use "mother"), not "root" or "parent
    sauce".

**Derivation**
:   The relation from a preparation to the candidate its opening paragraph
    states. Not "relationship", "edge", or "link".

**Candidate**
:   One name a stated parent may use: any name of a catalogued preparation,
    or a mother. Not "option" or "match".

**Chain**
:   The derivations walked from a preparation through its parents. A chain
    terminates, because no preparation is its own ancestor. Not "lineage" or
    "path".

**Resolved**
:   A preparation whose derivation the parser found. Its `parent` is set.

**Unresolved**
:   A preparation whose opening paragraph states no candidate, or states more
    than one. Its `parent` is `None`. This states an absence of evidence and
    never evidence of absence. Not "missing", "unknown", or "no parent" —
    each of those reads as a fact about the preparation rather than about
    what the source said.

**Ambiguous**
:   An opening paragraph that states two or more candidates. The source
    stated both and chose neither, so the preparation is unresolved. Not
    "conflicting" or "uncertain", which describe the parser rather than the
    text.

## Extraction

**Extraction**
:   Reading structure out of a source. Not "parsing" (parsing is the
    mechanism), not "ingestion" (nothing is being consumed).

**Provenance**
:   The `SourceRef` every preparation carries: source, entry number, and
    line. Not "citation" or "reference".

**Sauce chapter**
:   A chapter the source itself titles as sauces. Escoffier has three. An
    entry that does not say "sauce" in its own heading qualifies only inside
    one. Not "section" or "sauce section".

## Names this project does not use

**`shortorder`**
:   The rejected project name. It promised speed where this project promises
    composition. It appears in no file.

**"config"**
:   Use the specific noun: `Paths`, a rule set, a gate. "Config" names nothing.
