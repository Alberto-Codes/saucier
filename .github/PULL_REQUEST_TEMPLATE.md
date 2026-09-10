<!--
Remove every HTML comment before you submit. Keep the visible content.

TITLE

This repository squashes and takes the commit subject from the pull request
title. The squash body is blank. So release-please reads the title and nothing
else.

Format: type(scope): description
Under 50 characters, imperative mood.

Types:  feat | fix | docs | refactor | test | chore | perf | ci
Scopes: domain | ports | services | adapters | cli | extraction | corpus |
        docs | gates | ci

  feat(extraction): read the derivation clause of a mother
  fix(corpus): restore the entry lost to the scan blind spot

Do not put issue numbers in the scope. It breaks release-please.

  fix(20-mother-binding): ...   <- wrong, a scope is a noun, not a number

BREAKING CHANGES: THE `!` MARKER

Write `!` after the scope when the change breaks a published surface. A
published surface is the CLI, the interchange format, a domain entity, or a
count that the documentation quotes.

`release-please-config.json` sets `bump-minor-pre-major: true`, and the version
is below 1.0.0. So `!` raises a patch bump to a minor bump.

  fix(domain): reject mother bindings to derivatives that state the mother
    -> 0.6.0 becomes 0.6.1
  fix(domain)!: reject mother bindings to derivatives that state the mother
    -> 0.6.0 becomes 0.7.0

Release 0.7.0 nearly shipped as 0.6.1 because that title omitted the `!`.

A `BREAKING CHANGE:` footer in this body does not reach release-please. The
squash discards the body. The marker in the title is the only signal.

WHICH BUMP EACH TITLE PRODUCES

  feat(scope):   -> minor
  fix(scope):    -> patch
  any scope + !  -> minor, while the version stays below 1.0.0

After merge, release-please opens a release pull request. It creates the
release as a draft. Nothing reaches PyPI until a person publishes it.
-->

## Why

<!-- What problem does this solve? Contrast with the previous behaviour. -->

## What changed

<!-- 2-4 bullets, imperative mood. -->

-

## How to verify

<!-- A command, manual steps, or "CI only". -->

Test: `uv run pytest`

## Checks

- [ ] `uv run pre-commit run --all-files` passes
- [ ] Any new term has a glossary entry in this change
- [ ] No extraction rule guesses: unresolved stays unresolved
- [ ] If this changes the published counts, the affected docs are updated
- [ ] A breaking change carries `!` after the scope in the title

## Review focus

<!-- Where should a reviewer concentrate? State the known limits. -->

## Related

<!-- Issues, ADRs, or other pull requests that give context. -->

Closes #
