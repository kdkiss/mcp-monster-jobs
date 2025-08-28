from __future__ import annotations
"""Enable ``python -m job_scraper_server`` execution.

The reproduction plan specifies a ``main.py`` CLI entry-point that spawns the
Smithery-compliant job-scraper server.  Python packages are, however, also
commonly launched via the *module-as-script* mechanism::

    python -m job_scraper_server --host 0.0.0.0 --port 5555

This tiny *dunder-main* module delegates straight to
:pyfile:`job_scraper_server.main`, keeping the single-source-of-truth for CLI
argument handling while providing an additional, idiomatic execution avenue.
"""

from importlib import import_module
import sys
from types import ModuleType
from typing import List


def _forward_to_main(argv: List[str]) -> None:  # pragma: no cover – trivial wrapper
    """Import :pymod:`job_scraper_server.main` and execute its *main* function.

    ``main.py`` already provides an executable script style guard::

        if __name__ == "__main__":
            main()

    We therefore simply *import* the module so its top-level code can parse
    ``sys.argv``.  The function returns whatever the imported module exits
    with (usually :pycode:`None`).
    """

    # Temporarily replace *sys.argv* so that ``main.py`` sees the same list a
    # user would expect when invoking ``python -m job_scraper_server``.
    # ``sys.argv[0]`` should reflect the *command*, not the file path.
    original_argv = sys.argv
    sys.argv = ["job_scraper_server"] + argv[1:]
    try:
        import_module("job_scraper_server.main")
    finally:
        # Restore original argv for downstream code or tests.
        sys.argv = original_argv


# ---------------------------------------------------------------------------
# Execution guard
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover – manual invocation only
    _forward_to_main(sys.argv)
