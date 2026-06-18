"""Central access to Rook configuration."""

import json
import sys
from pathlib import Path
from typing import Any

from clisops.config import get_config as _get_clisops_config
from clisops.config import reload_config as _reload_clisops_config


_PACKAGE_FILE = Path(__file__)
CONFIG = _get_clisops_config(_PACKAGE_FILE)


def get_config() -> dict[str, Any]:
    """Return the current Rook configuration."""
    return CONFIG


def reload_config() -> dict[str, Any]:
    """Reload Rook configuration from the standard clisops sources."""
    global CONFIG

    CONFIG = _reload_clisops_config(_PACKAGE_FILE)

    # Keep the public compatibility alias current without making config depend
    # on importing the rest of Rook.
    rook_module = sys.modules.get("rook")
    if rook_module is not None:
        rook_module.CONFIG = CONFIG

    return CONFIG


def get_project_config(project: str) -> dict[str, Any]:
    """Return configuration for a project, or an empty mapping."""
    config = get_config().get(f"project:{project}", {})
    return config if isinstance(config, dict) else {}


def get_s3_storage_options() -> dict[str, Any]:
    """Build shared fsspec S3 transport options from Rook configuration."""
    config = get_config().get("s3", {})
    if not isinstance(config, dict):
        return {}

    options: dict[str, Any] = {}

    raw_options = config.get("storage_options_json")
    if raw_options:
        options.update(_parse_json_dict(raw_options))

    raw_client = config.get("client_kwargs_json")
    if raw_client:
        client_options = _parse_json_dict(raw_client)
        if client_options:
            options.setdefault("client_kwargs", {}).update(client_options)

    endpoint_url = config.get("endpoint_url")
    if endpoint_url:
        options.setdefault("client_kwargs", {})["endpoint_url"] = endpoint_url

    for key in ("anon", "key", "secret", "token"):
        value = config.get(key)
        if value is None or value == "":
            continue
        options[key] = _coerce_bool(value) if key == "anon" else value

    return options


def get_storage_base(project: str) -> str | None:
    """Return the preferred processing root for a project."""
    project_config = get_project_config(project)
    s3_config = get_config().get("s3", {})
    global_s3_base = (
        s3_config.get("base_dir") if isinstance(s3_config, dict) else None
    )
    return (
        project_config.get("s3_base_dir")
        or global_s3_base
        or project_config.get("base_dir")
    )


def _parse_json_dict(value: Any) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _coerce_bool(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return value
