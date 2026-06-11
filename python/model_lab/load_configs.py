"""Load Model Lab YAML configuration files.

The loader uses PyYAML when available and falls back to a small parser that
supports the simple scalar and list syntax used by the Stage 5.1 config files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from utils.paths import PROJECT_ROOT


CONFIG_DIR = PROJECT_ROOT / "config"
BACKTESTING_CONFIG = CONFIG_DIR / "backtesting.yaml"
SCORING_WEIGHTS_CONFIG = CONFIG_DIR / "scoring_weights.yaml"
TOURNAMENT_CONFIG = CONFIG_DIR / "tournament.yaml"


def _parse_scalar(value: str) -> Any:
    """Parse simple YAML scalar values used by local config files."""

    value = value.strip()
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _fallback_yaml_load(path: Path) -> dict[str, Any]:
    """Load a minimal YAML subset without adding a runtime dependency."""

    config: dict[str, Any] = {}
    current_key: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue

        stripped = line.strip()
        if stripped.startswith("-"):
            if current_key is None:
                raise ValueError(f"List item without key in {path}: {line}")
            config.setdefault(current_key, []).append(_parse_scalar(stripped[1:]))
            continue

        key, separator, value = stripped.partition(":")
        if not separator:
            raise ValueError(f"Invalid YAML line in {path}: {line}")

        current_key = key.strip()
        value = value.strip()
        config[current_key] = [] if value == "" else _parse_scalar(value)

    return config


def load_yaml_config(path: Path) -> dict[str, Any]:
    """Load one YAML configuration file."""

    try:
        import yaml  # type: ignore
    except ImportError:
        return _fallback_yaml_load(path)

    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected mapping at top level in {path}")
    return loaded


def load_all_configs() -> dict[str, dict[str, Any]]:
    """Load all Stage 5.1 Model Lab configuration files."""

    return {
        "backtesting": load_yaml_config(BACKTESTING_CONFIG),
        "scoring_weights": load_yaml_config(SCORING_WEIGHTS_CONFIG),
        "tournament": load_yaml_config(TOURNAMENT_CONFIG),
    }
