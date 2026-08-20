# ADR-0004: Source material is committed, derived output is not

## Status

Accepted.

## Date

2026-08-19

## Context

This repository is tagged once per published blog post. A reader checks out a
tag to stand where the post stands. That promise fails if the tag does not run,
and it fails quietly if the reader's data differs from the author's.

Three options were available for the Escoffier text.

A fetch script keeps the repository small, and it is the only option for a
large or restrictively licensed corpus. It adds a network step to the first
command a reader runs. It also rots, because a source can move or change.

A URL manifest is how several academic video datasets ship. It has the same
problems and adds one more. Readers can silently receive different bytes than
the author had.

Committing the text costs 2 MB. Project Gutenberg ebook 71395 is public domain
and redistributable, so nothing prevents it.

Derived output is a separate question. The parsed catalogue is reproducible
from the corpus by one command. Storing it would create a second source of
truth, which can disagree with the first.

## Decision

**`corpus/` is tracked. `data/` is not.**

A clone runs with no fetch step, and every reader parses the same bytes the
author parsed.

Three rules govern what may enter `corpus/`.

**Only redistributable material.** United States public domain currently covers
publication through 1930. Project Gutenberg texts are already cleared and carry
a licence wrapper, which the reader strips at load time rather than at commit
time. Copyrighted sources may be analysed and their findings published, because
that is transformative. They may not be committed.

**Only material small enough to commit.** The pre-commit hooks cap an added
file at 4 MB. A corpus above that gets a fetch script and stays untracked. The
Epic-Kitchens video corpus is the known future case, and it is both too large
and non-commercially licensed.

**Licensing is recorded per source.** Code is MIT. Corpus terms are documented
separately, so a restrictive dataset licence never silently constrains what the
implementation may become.

Anything reproducible from `corpus/` belongs in `data/` and stays untracked.

## Consequences

### Positive

- `git clone` then `uv sync` then `uv run saucier parse` works offline.
- Every reader gets identical bytes, so a per-post tag means what it claims.
- Tests run against the real source with no network and no fixtures that drift
  from it.

### Negative

- The repository carries 2 MB it would not otherwise carry, and each future
  committed source adds more.
- The rule needs judgement at the boundary. A 3 MB public domain text passes
  the size check and still deserves discussion.
- Two mechanisms will eventually coexist, because the video corpus must be
  fetched. Readers will meet both.

## References

- [Add a source](../how-to/add-a-source.md)
- [Contributing](https://github.com/Alberto-Codes/saucier/blob/main/CONTRIBUTING.md)
