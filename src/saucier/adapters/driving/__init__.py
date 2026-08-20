"""Driving adapters: entry points that call into the application.

A driving adapter parses whatever the outside world hands it, calls a
service, and renders the result. It holds no rules of its own, so the same
extraction is reachable from a CLI, a job runner, or a test.

Attributes:
    cli: The `saucier` command line interface, built on `argparse` so the
        package carries no runtime dependency.

Examples:
    Invoke the interface in process:

    ```python
    from saucier.adapters.driving.cli import main

    exit_code = main(["tree", "espagnole"])
    ```

See Also:
    - [saucier.services][]: What the entry points call into.
"""
