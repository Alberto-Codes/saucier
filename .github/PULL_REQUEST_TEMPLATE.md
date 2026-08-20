<!--
PR title becomes the squash commit subject. Under 50 chars, imperative.
Format: type(scope): description
Types: feat | fix | docs | refactor | test | chore | perf
Scopes: domain | ports | services | adapters | cli | extraction | corpus |
        docs | gates | ci
Do not put issue numbers in the scope. It breaks release-please.
-->

## Why

<!-- What problem does this solve? Contrast with the previous behaviour. -->

## What changed

<!-- 2-4 bullets, imperative mood. -->

## Checks

- [ ] `uv run pre-commit run --all-files` passes
- [ ] Any new term has a glossary entry in this change
- [ ] No extraction rule guesses: unresolved stays unresolved
- [ ] If this changes the published counts, the affected docs are updated
