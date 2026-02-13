"""Config loading and precedence resolution for manual-to-ppt CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

AUTO_LOGO_FILENAME = "CellGenTech_Logo_20221203_Blue_Horizontal.png"
DEFAULT_COLOR_SCHEME: dict[str, tuple[int, int, int]] = {
    "primary": (0, 102, 204),
    "accent": (51, 153, 255),
    "dark": (0, 51, 102),
    "light_bg": (240, 248, 255),
    "gray": (100, 100, 100),
}


class ConfigError(ValueError):
    """Raised for invalid config values or loading errors."""


def load_config(config_path: str | None) -> tuple[dict[str, Any], Path | None]:
    """Load JSON config. Returns empty config when not provided."""
    if not config_path:
        return {}, None

    path = _resolve_path(Path(config_path), base_dir=Path.cwd())
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    if not path.is_file():
        raise ConfigError(f"Config path is not a file: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid config JSON: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Failed to read config file: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError("Config JSON must be an object.")

    _validate_config(data)
    return data, path.parent


def resolve_runtime_config(
    excel_path: str | Path,
    cli_output: str | None,
    cli_output_dir: str | None,
    cli_logo: str | None,
    config: dict[str, Any],
    config_base_dir: Path | None = None,
) -> dict[str, Any]:
    """Resolve runtime settings using CLI > config > defaults precedence."""
    excel = Path(excel_path).expanduser().resolve()
    output_path = _resolve_output_path(excel, cli_output, cli_output_dir, config, config_base_dir)
    logo_path = _resolve_logo_path(excel, cli_logo, config, config_base_dir)
    color_scheme = _resolve_color_scheme(config.get("color_scheme"))
    return {
        "output_path": str(output_path),
        "logo_path": str(logo_path) if logo_path else None,
        "color_scheme": color_scheme,
    }


def _validate_config(config: dict[str, Any]) -> None:
    if "default_output_dir" in config and not isinstance(config["default_output_dir"], str):
        raise ConfigError("config.default_output_dir must be a string.")
    if "logo_path" in config and not isinstance(config["logo_path"], str):
        raise ConfigError("config.logo_path must be a string.")

    if "color_scheme" in config:
        color_scheme = config["color_scheme"]
        if not isinstance(color_scheme, dict):
            raise ConfigError("config.color_scheme must be an object.")
        for key, value in color_scheme.items():
            if key not in DEFAULT_COLOR_SCHEME:
                raise ConfigError(f"config.color_scheme.{key} is not a supported key.")
            _validate_rgb_triplet(value, f"config.color_scheme.{key}")


def _validate_rgb_triplet(value: Any, field_name: str) -> None:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ConfigError(f"{field_name} must be an RGB triplet.")
    for component in value:
        if not isinstance(component, int) or component < 0 or component > 255:
            raise ConfigError(f"{field_name} values must be integers between 0 and 255.")


def _resolve_output_path(
    excel_path: Path,
    cli_output: str | None,
    cli_output_dir: str | None,
    config: dict[str, Any],
    config_base_dir: Path | None,
) -> Path:
    if cli_output:
        return _resolve_path(Path(cli_output), config_base_dir or Path.cwd())
    if cli_output_dir:
        base_dir = _resolve_path(Path(cli_output_dir), config_base_dir or Path.cwd())
        return base_dir / f"{excel_path.stem}.pptx"

    default_output_dir = config.get("default_output_dir")
    if default_output_dir:
        base_dir = _resolve_path(Path(default_output_dir), config_base_dir or Path.cwd())
        return base_dir / f"{excel_path.stem}.pptx"

    return excel_path.with_suffix(".pptx")


def _resolve_logo_path(
    excel_path: Path,
    cli_logo: str | None,
    config: dict[str, Any],
    config_base_dir: Path | None,
) -> Path | None:
    if cli_logo:
        logo_path = _resolve_path(Path(cli_logo), config_base_dir or Path.cwd())
        if not logo_path.exists():
            raise ConfigError(f"Logo file not found: {logo_path}")
        return logo_path

    config_logo = config.get("logo_path")
    if config_logo:
        logo_path = _resolve_path(Path(config_logo), config_base_dir or Path.cwd())
        if not logo_path.exists():
            raise ConfigError(f"Logo file not found: {logo_path}")
        return logo_path

    for candidate in _auto_logo_candidates(excel_path):
        if candidate.exists():
            return candidate
    return None


def _auto_logo_candidates(excel_path: Path) -> list[Path]:
    repo_root = Path(__file__).resolve().parents[3]
    return [
        excel_path.parent / AUTO_LOGO_FILENAME,
        repo_root / "05_mail" / AUTO_LOGO_FILENAME,
        Path.cwd() / AUTO_LOGO_FILENAME,
    ]


def _resolve_color_scheme(color_scheme: Any) -> dict[str, tuple[int, int, int]]:
    resolved = dict(DEFAULT_COLOR_SCHEME)
    if not color_scheme:
        return resolved

    assert isinstance(color_scheme, dict)
    for key, value in color_scheme.items():
        _validate_rgb_triplet(value, f"config.color_scheme.{key}")
        resolved[key] = (int(value[0]), int(value[1]), int(value[2]))
    return resolved


def _resolve_path(path: Path, base_dir: Path) -> Path:
    candidate = path.expanduser()
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    return candidate.resolve()

