# API

Generated from the docstrings by `scripts/gen_ref_pages.py`. No page here is
written by hand, so none of them can drift from the code.

The packages follow the layer rule that `lint-imports` enforces. Read them in
this order to see which way the dependencies point.

- [`saucier.domain`](saucier/domain/index.md) — the frozen entities, value
  objects, and errors. It imports nothing of ours.
- [`saucier.ports`](saucier/ports/index.md) — the Protocols. They import the
  domain and nothing else.
- [`saucier.services`](saucier/services/index.md) — orchestration. It imports
  ports and domain, never an adapter.
- [`saucier.adapters`](saucier/adapters/index.md) — the source readers, the
  stores, and the CLI. Each one implements a port.
- [`saucier.infrastructure`](saucier/infrastructure/index.md) — configuration
  and the assembly root that wires the rest together.

Start at [`saucier`](saucier/index.md) for the package itself. The argument for
the layers lives in [Why the layers](../../explanation/hexagon.md).
