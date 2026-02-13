"""Legacy compatibility wrapper for manual-to-ppt conversion."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

_core_convert_excel_to_ppt = None


def _ensure_manual_to_ppt_path() -> Path:
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parents[1]
    skill_root = repo_root / "skills" / "manual-to-ppt"
    if str(skill_root) not in sys.path:
        sys.path.insert(0, str(skill_root))
    return skill_root


def _get_core_convert():
    global _core_convert_excel_to_ppt
    if _core_convert_excel_to_ppt is None:
        _ensure_manual_to_ppt_path()
        from manual_to_ppt.converter import convert_excel_to_ppt as core_convert

        _core_convert_excel_to_ppt = core_convert
    return _core_convert_excel_to_ppt


def convert_excel_to_ppt(
    excel_path: str | Path,
    output_path: str | Path,
    temp_dir: str | Path = "temp/images",
    logo_path: str | None = None,
) -> bool:
    """Backward-compatible conversion function returning bool."""
    core_convert = _get_core_convert()
    summary: Any = core_convert(
        excel_path=excel_path,
        output_path=output_path,
        temp_dir=temp_dir,
        logo_path=logo_path,
    )
    if isinstance(summary, dict):
        return bool(summary.get("success"))
    return bool(summary)


def main() -> int:
    """Backward-compatible no-arg CLI behavior."""
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    excel_path = project_dir / "相見積操作マニュアル.xlsx"
    output_path = project_dir / "相見積操作マニュアル.pptx"
    temp_dir = project_dir / "temp" / "images"
    logo_path = project_dir / "CellGenTech_Logo_20221203_Blue_Horizontal.png"

    if not excel_path.exists():
        print(f"ERROR: Excel file not found: {excel_path}")
        return 1

    resolved_logo = str(logo_path) if logo_path.exists() else None

    core_convert = _get_core_convert()
    summary = core_convert(
        excel_path=excel_path,
        output_path=output_path,
        temp_dir=temp_dir,
        logo_path=resolved_logo,
    )
    success = bool(summary.get("success")) if isinstance(summary, dict) else bool(summary)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())

