"""Check that the shipped client configs only ask for modules HuRI lists.

    python scripts/check_config_modules.py <registry.toml> [config/client_*.yaml ...]

<registry.toml> is huri-modules' registry of curated modules (CI downloads it
at HURI_MODULES_REF). Each `modules.<tag>.name` of a config must be the
`name` of a `[[module]]` entry there; a module given by import path
(`module: pkg.mod:Class`) is not a curated one and is skipped. No network:
the configs are read with OmegaConf, which huri-core[client] brings.
Exits 1 on an unknown name, 2 on bad usage.
"""

import sys
from pathlib import Path
from typing import Iterable, List, Set

from omegaconf import OmegaConf

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]


def registry_names(path: Path) -> Set[str]:
    with open(path, "rb") as f:
        registry = tomllib.load(f)
    return {entry["name"] for entry in registry.get("module", [])}


def unknown_modules(config: Path, known: Set[str]) -> List[str]:
    raw = OmegaConf.to_container(OmegaConf.load(config), resolve=False)
    assert isinstance(raw, dict)
    modules = raw.get("modules") or {}
    return [
        f"{config.name}: modules.{tag}.name = {spec['name']!r}"
        for tag, spec in modules.items()
        if "name" in spec and spec["name"] not in known
    ]


def main(argv: Iterable[str]) -> int:
    args = list(argv)
    if not args:
        print(__doc__, file=sys.stderr)
        return 2
    registry = Path(args[0])
    configs = [Path(a) for a in args[1:]] or sorted(
        (ROOT / "config").glob("client_*.yaml")
    )
    known = registry_names(registry)
    if not known:
        print(f"{registry}: no [[module]] entry", file=sys.stderr)
        return 2
    bad = [line for config in configs for line in unknown_modules(config, known)]
    for line in bad:
        print(f"not in {registry.name}: {line}", file=sys.stderr)
    if not bad:
        print(f"ok: {len(configs)} config(s) against {len(known)} registered modules")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
