# Security

## Scope

`saucier` reads text files that ship with the repository and writes JSON to a
local directory. It opens no network connections, executes no remote code, and
takes no credentials. It has no runtime dependencies.

The realistic risks are therefore narrow: a malicious source file that drives
the parser into pathological behaviour, or a supply-chain problem in a
development dependency.

## Reporting

Report a vulnerability through GitHub's private advisory form:
[Security → Report a vulnerability](https://github.com/Alberto-Codes/saucier/security/advisories/new).

Do not open a public issue for a vulnerability.

Expect an acknowledgement within seven days. This is a single-maintainer
project, so a fix timeline depends on severity.

## Supported versions

The most recent release only. Each tag corresponds to a published blog post
and is immutable, so fixes ship forward as a new patch tag rather than as an
amendment to an old one.

## Dependency audit

`uv-secure` runs on every push before work leaves a machine, and again in CI.
