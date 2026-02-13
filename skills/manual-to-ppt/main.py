"""Official CLI entrypoint for manual-to-ppt skill."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from manual_to_ppt.config_loader import ConfigError, load_config, resolve_runtime_config
from manual_to_ppt.converter import convert_excel_to_ppt

VALID_EXCEL_SUFFIXES = {".xlsx", ".xlsm", ".xltx", ".xltm"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert an Excel manual to a PowerPoint deck.")
    parser.add_argument("excel_path", nargs="?", help="Path to source Excel file.")
    parser.add_argument("--output", help="Output .pptx path.")
    parser.add_argument("--output-dir", help="Directory for output .pptx.")
    parser.add_argument("--logo", help="Logo image path.")
    parser.add_argument("--config", help="Path to config JSON.")
    parser.add_argument("--interactive", action="store_true", help="Prompt missing options interactively.")
    return parser


def _prompt_if_missing(value: str | None, prompt: str) -> str | None:
    if value:
        return value
    entered = input(prompt).strip()
    return entered or None


def _apply_interactive_defaults(args: argparse.Namespace) -> argparse.Namespace:
    args.excel_path = _prompt_if_missing(args.excel_path, "Excel path: ")
    if not args.output and not args.output_dir:
        args.output = _prompt_if_missing(args.output, "Output .pptx path (optional): ")
    args.logo = _prompt_if_missing(args.logo, "Logo path (optional): ")
    args.config = _prompt_if_missing(args.config, "Config JSON path (optional): ")
    return args


def _validate_inputs(args: argparse.Namespace) -> Path:
    if args.output and args.output_dir:
        raise ConfigError("Cannot use --output and --output-dir together.")
    if not args.excel_path:
        raise ConfigError("excel_path is required.")

    excel_path = Path(args.excel_path).expanduser().resolve()
    if not excel_path.exists():
        raise ConfigError(f"Excel file not found: {excel_path}")
    if excel_path.suffix.lower() not in VALID_EXCEL_SUFFIXES:
        raise ConfigError(f"Unsupported Excel extension: {excel_path.suffix}")
    return excel_path


def _print_summary(summary: dict[str, Any]) -> None:
    required = ("steps_count", "slides_count", "output_path")
    for key in required:
        if key not in summary:
            raise RuntimeError(f"Missing required summary key: {key}")
    line = {
        "steps_count": int(summary["steps_count"]),
        "slides_count": int(summary["slides_count"]),
        "output_path": str(summary["output_path"]),
    }
    print(json.dumps(line, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.interactive:
            args = _apply_interactive_defaults(args)

        excel_path = _validate_inputs(args)
        config, config_base_dir = load_config(args.config)
        runtime_config = resolve_runtime_config(
            excel_path=excel_path,
            cli_output=args.output,
            cli_output_dir=args.output_dir,
            cli_logo=args.logo,
            config=config,
            config_base_dir=config_base_dir,
        )

        output_path = Path(runtime_config["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = excel_path.parent / "temp" / "images"

        summary = convert_excel_to_ppt(
            excel_path=excel_path,
            output_path=output_path,
            temp_dir=temp_dir,
            logo_path=runtime_config["logo_path"],
            color_scheme=runtime_config["color_scheme"],
        )
        _print_summary(summary)
        return 0 if bool(summary.get("success")) else 1
    except ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

