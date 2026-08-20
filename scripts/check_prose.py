"""Prose gate: strict-mode pages obey the writing system.

The writing system in `CLAUDE.md` is distilled from ASD-STE100. Guidance
drifts across a long series, so the mechanical rules are checked rather
than trusted: no semicolons, at most one em-dash per paragraph, sentences
within the word cap, and no marketing adjectives.

Only strict-mode surfaces are gated. Explanation pages are flavored mode,
where range and analogy are allowed, so they are left alone. Fenced code
blocks and inline code are skipped everywhere, because a semicolon in a
shell snippet is not prose.

Examples:
    Run against the strict-mode pages:

    ```console
    $ uv run python scripts/check_prose.py
    checked 3 files
    ```
"""

from __future__ import annotations

import re
from pathlib import Path

STRICT = ("README.md", "docs/reference")
"""Surfaces where a misread costs cycles. Explanation pages are exempt."""

MAX_WORDS = 25
"""Descriptive sentences cap here. Instructions should be shorter still."""

MAX_EM_DASHES = 1
"""Per paragraph, not per page."""

MARKETING = frozenset(
    {
        "seamless",
        "seamlessly",
        "robust",
        "powerful",
        "blazing",
        "cutting-edge",
        "state-of-the-art",
        "effortless",
        "revolutionary",
        "leverage",
        "leverages",
        "utilize",
        "utilizes",
    }
)
"""Adjectives that assert instead of showing. State the number instead."""

_FENCE = re.compile(r"^\s*```")
_INLINE_CODE = re.compile(r"`[^`]*`")
_LINK_TARGET = re.compile(r"\]\([^)]*\)")
_TABLE_ROW = re.compile(r"^\s*\|")
_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.|:)\s")
_SENTENCE = re.compile(r"[.!?]+(?:\s|$)")


def strict_files(root: Path) -> list[Path]:
    """Collect the markdown pages the strict rules apply to.

    Args:
        root: Repository root.

    Returns:
        Strict-mode markdown files, sorted for stable output.
    """
    found: set[Path] = set()
    for entry in STRICT:
        target = root / entry
        if target.is_file():
            found.add(target)
        elif target.is_dir():
            found.update(target.rglob("*.md"))
    return sorted(found)


def prose_paragraphs(text: str) -> list[str]:
    """Split a page into paragraphs, dropping code and table rows.

    A list item is its own unit. Items sit on adjacent lines, so treating a
    list as one paragraph would charge it the em-dash budget of a single
    sentence and concatenate its items into one false long sentence.

    Args:
        text: The page's full markdown.

    Returns:
        Paragraphs of prose, with inline code and link targets removed.
    """
    units: list[str] = []
    buffer: list[str] = []
    fenced = False

    def flush() -> None:
        """Move the buffered lines into the unit list."""
        if buffer:
            units.append(" ".join(buffer).strip())
            buffer.clear()

    for line in text.splitlines():
        if _FENCE.match(line):
            fenced = not fenced
            flush()
            continue
        if fenced or _TABLE_ROW.match(line):
            continue
        stripped = _LINK_TARGET.sub("]", _INLINE_CODE.sub("CODE", line))
        if not stripped.strip() or _LIST_ITEM.match(stripped):
            flush()
        if stripped.strip():
            buffer.append(stripped.strip())
    flush()
    return [u for u in units if u]


def paragraph_findings(paragraph: str) -> list[str]:
    """Check one paragraph against every mechanical rule.

    Args:
        paragraph: One paragraph of prose.

    Returns:
        A description of each rule the paragraph breaks.
    """
    findings: list[str] = []
    if ";" in paragraph:
        findings.append("semicolon")
    dashes = paragraph.count("—")
    if dashes > MAX_EM_DASHES:
        findings.append(f"{dashes} em-dashes in one paragraph")
    findings.extend(
        f"marketing adjective {word!r}"
        for word in sorted(MARKETING)
        if re.search(rf"\b{re.escape(word)}\b", paragraph, re.IGNORECASE)
    )
    findings.extend(_long_sentences(paragraph))
    return findings


def _long_sentences(paragraph: str) -> list[str]:
    """Report sentences over the word cap.

    Args:
        paragraph: One paragraph of prose.

    Returns:
        A description of each sentence that exceeds the cap.
    """
    sentences = (s.split() for s in _SENTENCE.split(paragraph))
    return [
        f"{len(words)}-word sentence: {' '.join(words[:8])}..."
        for words in sentences
        if len(words) > MAX_WORDS
    ]


def main() -> int:
    """Run the gate over every strict-mode page.

    Returns:
        Process exit code: 0 when clean, 1 when any rule is broken.
    """
    root = Path(__file__).resolve().parent.parent
    files = strict_files(root)
    failed = False
    for path in files:
        for paragraph in prose_paragraphs(path.read_text(encoding="utf-8")):
            for finding in paragraph_findings(paragraph):
                rel = path.relative_to(root)
                print(f"FAIL {rel}: {finding}")
                failed = True
    print(f"checked {len(files)} files")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
