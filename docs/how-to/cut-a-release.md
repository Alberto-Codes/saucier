# Cut a release

release-please cuts every release from the commit history. You never edit a
version by hand. The release is created as a **draft**, so nothing reaches
PyPI or Pages until you publish it yourself. This page shows what runs, in
what order, and where you are expected to intervene.

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
5. Merging the release PR makes release-please create a **draft** GitHub
   Release. A draft carries no tag, so nothing downstream runs.
6. You edit the draft notes, then publish it by hand.
7. Publishing creates the tag. `publish.yml` uploads to PyPI over OIDC, and
   `docs.yml` deploys the site to GitHub Pages.

</details>

## What the draft is for

The release notes should say what this tag is in the series and link the post
that describes it. The post does not exist when the code merges. A draft holds
the release open until both are ready.

Keep the notes short. The generated CHANGELOG already lists what changed. Add
what it cannot say: the state this tag represents, the command that
demonstrates it, and a link.

## Why the token still matters

GitHub does not start a workflow from an event that `GITHUB_TOKEN` created.
The rule stops a workflow triggering itself forever.

Publishing a draft is your action rather than a token's, so the tag triggers
`publish.yml` either way. The token still matters for the `update-lockfile`
commit. Pushed with `GITHUB_TOKEN`, it will not re-run CI on the release PR,
so the PR shows a passing run for the wrong commit.

`release-please.yml` fails a cut with no token set, rather than reporting a
success that is only partly true.

```yaml
- name: Fail a release cut without the PAT
  if: steps.release.outputs.release_created == 'true' && env.HAS_PAT != 'true'
```

Set `RELEASE_PLEASE_TOKEN` to a personal access token with `contents: write`
and `pull-requests: write`.

**Verify on the first cut** that merging the release PR produces a draft with
no tag. If a tag appears before you publish, the draft setting is not doing
what this page claims and the flow above needs correcting.

## Why the lockfile job exists

release-please bumps the version in `pyproject.toml`. It does not touch
`uv.lock`, which records the same version. The release PR would then fail its
own `uv lock --check`, and the failure would read as a lockfile problem rather
than a release-tooling one.

## What you control

The commit subjects and the draft notes. `feat` bumps the minor version. `fix`
bumps the patch. `release-please-config.json` maps each type to a CHANGELOG
section.

Version numbers and post numbers drift apart, because release-please counts
change types and the series counts posts. Post three may be `v0.5.0`. Posts
therefore name their tag rather than a version number.

Tags are immutable. A bug in a published tag gets a new patch tag and a note.
