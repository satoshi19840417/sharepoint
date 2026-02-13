from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CONVERT_WRAPPER = REPO_ROOT / "05_mail" / "scripts" / "convert_manual_to_ppt.py"
PARSE_WRAPPER = REPO_ROOT / "05_mail" / "scripts" / "parse_manual.py"
GENERATE_WRAPPER = REPO_ROOT / "05_mail" / "scripts" / "generate_ppt.py"


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_convert_wrapper_exposes_legacy_api():
    module = _load_module(CONVERT_WRAPPER, "legacy_convert_wrapper")
    assert hasattr(module, "convert_excel_to_ppt")
    assert callable(module.convert_excel_to_ppt)


def test_convert_wrapper_returns_bool(monkeypatch, tmp_path):
    module = _load_module(CONVERT_WRAPPER, "legacy_convert_wrapper_bool")
    excel_path = tmp_path / "manual.xlsx"
    output_path = tmp_path / "manual.pptx"
    excel_path.write_text("stub", encoding="utf-8")

    monkeypatch.setattr(
        module,
        "_core_convert_excel_to_ppt",
        lambda **kwargs: {"success": True, "steps_count": 1, "slides_count": 2, "output_path": str(output_path)},
    )
    assert module.convert_excel_to_ppt(excel_path, output_path) is True


def test_parse_and_generate_wrappers_expose_symbols():
    parse_module = _load_module(PARSE_WRAPPER, "legacy_parse_wrapper")
    generate_module = _load_module(GENERATE_WRAPPER, "legacy_generate_wrapper")
    assert hasattr(parse_module, "ExcelManualParser")
    assert hasattr(generate_module, "PowerPointGenerator")

