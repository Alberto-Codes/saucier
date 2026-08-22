# Glossary

One term per concept, one concept per term. These are the project's canonical
nouns. Docs, code identifiers, commit messages, and conversation use these
words and no synonyms for them. Coin a new term only with a new glossary entry
in the same change.

## What a source yields

**Work**
:   The book itself, across every edition of it. Named by the first half of a
    `source_id`, such as `escoffier`. Not "title" or "book".

**Edition**
:   A named revision of a work, as the work's own printing history states it.
    `New and Revised Edition, January 1909`. Not "version" or "release".

**Impression**
:   One printing of an edition, from the same setting and with no revision.
    `January 1920`. Not "edition" and not "reprint".

**Witness**
:   One text of one edition that this project can read: a transcription or a
    scan. Each source is a witness. A witness is evidence of the work rather
    than the work. Not "copy" or "version".

**Fidelity**
:   How a witness was obtained, and therefore how far its surface forms may
    be trusted. Two values: `transcription`, proofread by hand, and `ocr`,
    machine-read from a scan. Stated, never inferred. Not "quality" or
    "confidence".

**Source**
:   One document the extractor reads, identified by a `source_id` such as
    `escoffier-1909`. One source is one witness. Not "book", "text", or
    "file".

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

**Statement**
:   A candidate's name written as a whole run of words inside one sentence
    of the opening paragraph. Only a statement records a derivation. Not
    "mention" or "reference".

**Subject**
:   What an entry's own name denotes. A run of words inside the entry's own
    name states the subject, never a parent. A mother is never a subject.
    Not "topic".

**Shadow**
:   A statement lying entirely inside a longer statement that reaches a
    different preparation. A shadowed name is part of the longer statement
    and is not read on its own. Not "overlap".

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

## Comparison

**Difference**
:   One row of a comparison between two witnesses: a concept, what each
    witness holds, and the cause. Not "delta", "change", or "diff row".

**Cause**
:   Why two witnesses differ on one concept. Five values, and a row may carry
    more than one. `added` and `removed` mean one witness holds the concept
    and the other does not. `retitled` means one heading is the other plus
    whole words. `parent-changed` means a preparation records a different
    derivation in each witness. `ocr-suspected` means a scanned witness explains the row as
    well as a revision does. Not "reason", "kind", or "type".

## Names this project does not use

**`shortorder`**
:   The rejected project name. It promised speed where this project promises
    composition. It appears in no file.

**"config"**
:   Use the specific noun: `Paths`, a rule set, a gate. "Config" names nothing.
