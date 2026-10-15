"""scripts/check_config_modules.py, against a registry written here (offline)."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "check_config_modules", ROOT / "scripts" / "check_config_modules.py"
)
assert spec and spec.loader
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

# Every module name the shipped configs use, as huri-modules' registry lists
# them today.
NAMES = ["emo", "eag", "mov", "rag", "qag", "stt", "tag", "tts", "tts_cosyvoice"]


def registry(tmp_path, names):
    path = tmp_path / "registry.toml"
    path.write_text(
        "schema = 2\n"
        + "".join(f'\n[[module]]\nname = "{n}"\npackage = "p"\n' for n in names)
    )
    return path


def test_shipped_configs_use_registered_names(tmp_path):
    assert check.main([str(registry(tmp_path, NAMES + ["vad"]))]) == 0


def test_an_unregistered_name_is_reported(tmp_path, capsys):
    assert check.main([str(registry(tmp_path, NAMES))]) == 1  # vad missing
    assert "modules.vad.name = 'vad'" in capsys.readouterr().err


def test_a_module_by_import_path_is_skipped(tmp_path):
    config = tmp_path / "client_x.yaml"
    config.write_text("modules:\n  servo:\n    module: acme.servo:Servo\n")
    assert check.main([str(registry(tmp_path, ["rag"])), str(config)]) == 0


@pytest.mark.parametrize("argv", [[], None])
def test_bad_usage(tmp_path, argv):
    if argv is None:
        argv = [str(registry(tmp_path, []))]
    assert check.main(argv) == 2
