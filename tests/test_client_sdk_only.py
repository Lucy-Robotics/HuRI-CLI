"""huri-cli uses huri-core only through the client SDK (#12): its internals,
importable without Ray (plugins, compat), may change in a patch release."""

import ast
from pathlib import Path
from typing import Iterator, Optional, Set

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "huri_cli"
# huri-core's client SDK; replace by huri-core's recorded public surface once
# huri-core#156 is released.
CLIENT_SDK = {
    "huri_core.core.client",
    "huri_core.core.events",
    "huri_core.core.dataclasses.config",
}


def imports(source: str) -> Iterator[str]:
    """Absolute modules a file imports, at any depth (inside functions too)."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            # `from huri_core.core import plugins` imports a module too.
            if node.module in ("huri_core", "huri_core.core"):
                yield from (f"{node.module}.{alias.name}" for alias in node.names)
            else:
                yield node.module


def violations(path: Path, source: Optional[str] = None) -> Set[str]:
    if source is None:
        source = path.read_text()
    rel = path.relative_to(ROOT)
    return {
        f"{rel} imports {name}"
        for name in imports(source)
        if name.split(".")[0] == "huri_core" and name not in CLIENT_SDK
    }


def test_the_current_huri_cli_passes_the_client_only_check():
    found = set().union(*(violations(p) for p in PACKAGE.rglob("*.py")))
    assert not found, sorted(found)


@pytest.mark.parametrize(
    "module",
    [
        "huri_core.core.plugins",
        "huri_core.core.compat",
        "huri_core.core.huri",
        "huri_core.core.factory",
    ],
)
def test_an_import_of_a_huri_core_internal_fails_ci(module):
    main = PACKAGE / "main.py"
    source = main.read_text() + f"\n\ndef _late():\n    import {module}\n"
    assert violations(main, source) == {f"huri_cli/main.py imports {module}"}
