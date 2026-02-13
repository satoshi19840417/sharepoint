from __future__ import annotations

import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from manual_to_ppt.config_loader import (  # noqa: E402
    ConfigError,
    DEFAULT_COLOR_SCHEME,
    load_config,
    resolve_runtime_config,
)


def test_load_config_invalid_json_raises(tmp_path):
    config_path = tmp_path / "invalid.json"
    config_path.write_text("{invalid", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(str(config_path))


def test_resolve_runtime_config_precedence(tmp_path):
    excel_path = tmp_path / "manual.xlsx"
    excel_path.write_text("stub", encoding="utf-8")

    config_base_dir = tmp_path / "cfg"
    config_base_dir.mkdir(parents=True, exist_ok=True)
    config_logo = config_base_dir / "config-logo.png"
    config_logo.write_bytes(b"logo")

    cli_logo = tmp_path / "cli-logo.png"
    cli_logo.write_bytes(b"logo")

    config = {
        "default_output_dir": "config-out",
        "logo_path": "config-logo.png",
        "color_scheme": {"primary": [1, 2, 3]},
    }
    resolved = resolve_runtime_config(
        excel_path=excel_path,
        cli_output="custom/result.pptx",
        cli_output_dir="ignored-out-dir",
        cli_logo=str(cli_logo),
        config=config,
        config_base_dir=config_base_dir,
    )

    assert resolved["output_path"].endswith(str(Path("custom") / "result.pptx"))
    assert resolved["logo_path"] == str(cli_logo.resolve())
    assert resolved["color_scheme"]["primary"] == (1, 2, 3)


def test_resolve_runtime_config_auto_logo_and_default_output(tmp_path):
    excel_path = tmp_path / "manual.xlsx"
    excel_path.write_text("stub", encoding="utf-8")
    auto_logo = tmp_path / "CellGenTech_Logo_20221203_Blue_Horizontal.png"
    auto_logo.write_bytes(b"logo")

    resolved = resolve_runtime_config(
        excel_path=excel_path,
        cli_output=None,
        cli_output_dir=None,
        cli_logo=None,
        config={},
        config_base_dir=None,
    )

    assert resolved["output_path"] == str((tmp_path / "manual.pptx").resolve())
    assert resolved["logo_path"] == str(auto_logo.resolve())
    assert resolved["color_scheme"] == DEFAULT_COLOR_SCHEME

