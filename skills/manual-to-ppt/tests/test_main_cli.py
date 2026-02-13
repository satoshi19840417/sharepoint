from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_cli_module():
    skill_root = Path(__file__).resolve().parents[1]
    module_path = skill_root / "main.py"
    spec = importlib.util.spec_from_file_location("manual_to_ppt_cli", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_cli_success_prints_json_summary(monkeypatch, tmp_path, capsys):
    cli = _load_cli_module()
    excel_path = tmp_path / "manual.xlsx"
    excel_path.write_text("stub", encoding="utf-8")
    output_path = tmp_path / "result.pptx"

    def fake_convert_excel_to_ppt(*args, **kwargs):  # noqa: ANN002, ANN003
        return {
            "success": True,
            "steps_count": 2,
            "slides_count": 3,
            "output_path": str(output_path),
        }

    monkeypatch.setattr(cli, "convert_excel_to_ppt", fake_convert_excel_to_ppt)
    exit_code = cli.main([str(excel_path), "--output", str(output_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    summary_line = captured.out.strip().splitlines()[-1]
    summary = json.loads(summary_line)
    assert summary["steps_count"] == 2
    assert summary["slides_count"] == 3
    assert summary["output_path"] == str(output_path)


def test_cli_missing_excel_returns_2(tmp_path, capsys):
    cli = _load_cli_module()
    missing = tmp_path / "missing.xlsx"
    exit_code = cli.main([str(missing)])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "not found" in captured.err.lower()


def test_cli_invalid_config_returns_2(tmp_path, capsys):
    cli = _load_cli_module()
    excel_path = tmp_path / "manual.xlsx"
    excel_path.write_text("stub", encoding="utf-8")
    invalid_config = tmp_path / "invalid.json"
    invalid_config.write_text("{invalid", encoding="utf-8")

    exit_code = cli.main([str(excel_path), "--config", str(invalid_config)])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "invalid config json" in captured.err.lower()


def test_cli_output_and_output_dir_conflict_returns_2(tmp_path, capsys):
    cli = _load_cli_module()
    excel_path = tmp_path / "manual.xlsx"
    excel_path.write_text("stub", encoding="utf-8")

    exit_code = cli.main(
        [
            str(excel_path),
            "--output",
            str(tmp_path / "result.pptx"),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--output and --output-dir" in captured.err

