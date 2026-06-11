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
    """Load the small nested YAML subset used by local config files."""

    raw_lines = path.read_text(encoding="utf-8").splitlines()
    lines = [
        line.rstrip()
        for line in raw_lines
        if line.strip() and not line.lstrip().startswith("#")
    ]
    config: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, config)]

    def next_container_type(current_index: int, current_indent: int) -> type:
        """Infer whether an empty YAML key should hold a mapping or list."""

        for next_line in lines[current_index + 1 :]:
            next_indent = len(next_line) - len(next_line.lstrip(" "))
            if next_indent <= current_indent:
                break
            if next_line.strip().startswith("-"):
                return list
            return dict
        return dict

    for index, line in enumerate(lines):
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        while indent <= stack[-1][0]:
            stack.pop()

        parent = stack[-1][1]
        if stripped.startswith("-"):
            if not isinstance(parent, list):
                raise ValueError(f"List item without list parent in {path}: {line}")
            parent.append(_parse_scalar(stripped[1:].strip()))
            continue

        key, separator, value = stripped.partition(":")
        if not separator:
            raise ValueError(f"Invalid YAML line in {path}: {line}")
        if not isinstance(parent, dict):
            raise ValueError(f"Mapping item without mapping parent in {path}: {line}")

        key = key.strip()
        value = value.strip()
        if value:
            parent[key] = _parse_scalar(value)
            continue

        container_class = next_container_type(index, indent)
        container: dict[str, Any] | list[Any]
        container = [] if container_class is list else {}
        parent[key] = container
        stack.append((indent, container))

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
