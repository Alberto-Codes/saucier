# Cut a release

release-please cuts every release from the commit history. You never edit a
version by hand. This page shows what runs, in what order, and the one
condition that stops the second half.

## The flow

```mermaid
flowchart TD
    accTitle: How a merged change reaches PyPI and GitHub Pages
    accDescr {
        A pull request runs CI, which holds four jobs: lint, types, structure
        and test. Merging it to main starts release-please.yml. That workflow
        opens a release PR carrying the version bump and the CHANGELOG entry.
        The update-lockfile job then commits uv.lock onto the same release PR,
        because release-please bumps pyproject.toml and leaves the lockfile
        behind. Merging the release PR makes release-please cut a tag and a
        GitHub Release. What happens next depends on which token cut it. Cut
        with RELEASE_PLEASE_TOKEN, the tag and the release trigger two
        workflows in parallel: publish.yml builds and uploads to PyPI over
        OIDC, and docs.yml builds the site and deploys it to GitHub Pages. Cut
        with GITHUB_TOKEN, the tag still exists, but GitHub starts no workflow
        from it, so neither PyPI nor Pages updates. release-please.yml detects
        that case and fails its own run rather than reporting success.
    }

    pr["Pull request"] --> ci["ci.yml<br/>lint, types, structure, test"]
    ci --> main["Merge to main"]
    main --> rp["release-please.yml"]
    rp --> relpr["Release PR<br/>version bump and CHANGELOG"]
    relpr --> lock["update-lockfile job<br/>commits uv.lock"]
    lock --> mergerel["Merge the release PR"]
    mergerel --> token{"Which token<br/>cut the release?"}
    token -->|RELEASE_PLEASE_TOKEN| cut["Tag and GitHub Release<br/>start the next workflows"]
    token -->|GITHUB_TOKEN| stall(["Tag exists.<br/>No workflow starts.<br/>The run fails on purpose."])
    cut --> pypi(["publish.yml<br/>build, then PyPI over OIDC"])
    cut --> pages(["docs.yml<br/>mkdocs build, then Pages"])
```

<details markdown="1">
<summary>The same flow in text</summary>

1. A pull request runs `ci.yml`. It holds four jobs: lint, types, structure
   and test.
2. Merging to `main` starts `release-please.yml`.
3. release-please opens a release PR. The PR carries the version bump and the
   CHANGELOG entry.
4. The `update-lockfile` job commits `uv.lock` onto that same PR.
5. Merging the release PR makes release-please cut a tag and a GitHub Release.
6. Cut with `RELEASE_PLEASE_TOKEN`, the tag and the release start two
   workflows at once. `publish.yml` uploads to PyPI over OIDC. `docs.yml`
   deploys the site to GitHub Pages.
7. Cut with `GITHUB_TOKEN`, the tag still exists. GitHub starts no workflow
   from it, so neither PyPI nor Pages updates.
8. `release-please.yml` detects that case and fails its own run.

</details>

## Why the token decides

GitHub does not start a workflow from an event that `GITHUB_TOKEN` created.
The rule stops a workflow triggering itself forever. Here it means a release
cut with the default token produces a tag that reaches neither PyPI nor Pages.

The release looks green. Nothing ships. `release-please.yml` therefore fails
the run at that moment rather than later.

```yaml
- name: Fail a release cut without the PAT
  if: steps.release.outputs.release_created == 'true' && env.HAS_PAT != 'true'
```

Set `RELEASE_PLEASE_TOKEN` to a personal access token with `contents: write`
and `pull-requests: write`. Without it, push the tag by hand after the run
fails.

## Why the lockfile job exists

release-please bumps the version in `pyproject.toml`. It does not touch
`uv.lock`, which records the same version. The release PR would then fail its
own `uv lock --check`, and the failure would read as a lockfile problem rather
than a release-tooling one.

## What you control

Only the commit subjects. `feat` bumps the minor version. `fix` bumps the
patch. `release-please-config.json` maps each type to a CHANGELOG section.

Tags are immutable. A bug in a published tag gets a new patch tag and a note.
