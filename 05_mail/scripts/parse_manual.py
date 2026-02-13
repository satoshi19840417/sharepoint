"""Legacy compatibility wrapper for Excel manual parser."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


def _ensure_manual_to_ppt_path() -> Path:
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parents[1]
    skill_root = repo_root / "skills" / "manual-to-ppt"
    if str(skill_root) not in sys.path:
        sys.path.insert(0, str(skill_root))
    return skill_root


def __getattr__(name: str) -> Any:
    if name == "ExcelManualParser":
        _ensure_manual_to_ppt_path()
        from manual_to_ppt.parse_manual import ExcelManualParser

        return ExcelManualParser
    raise AttributeError(name)


def main() -> int:
    _ensure_manual_to_ppt_path()
    from manual_to_ppt.parse_manual import main as core_main

    return core_main()


if __name__ == "__main__":
    raise SystemExit(main())

