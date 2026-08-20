"""Generate the API reference pages and their navigation.

Every public module gets a page built from its docstrings, so the reference
section cannot drift from the code. `check_doc_refs.py` proves the dotted
paths resolve; this renders them.

Examples:
    Invoked by mkdocs, not by hand:

    ```console
    $ uv run mkdocs build --strict
    ```
"""

from pathlib import Path

import mkdocs_gen_files

NAV = mkdocs_gen_files.Nav()
ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"
OUT = Path("reference", "api")

for path in sorted(SRC.rglob("*.py")):
    module_path = path.relative_to(SRC).with_suffix("")
    doc_path = path.relative_to(SRC).with_suffix(".md")
    full_doc_path = OUT / doc_path
    parts = tuple(module_path.parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1].startswith("_"):
        continue

    if not parts:
        continue

    NAV[parts] = doc_path.as_posix()
    with mkdocs_gen_files.open(full_doc_path, "w") as page:
        page.write(f"::: {'.'.join(parts)}\n")
    mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(ROOT))

with mkdocs_gen_files.open(OUT / "SUMMARY.md", "w") as nav_file:
    nav_file.writelines(NAV.build_literate_nav())
