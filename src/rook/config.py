"""Central access to Rook configuration."""

import json
from pathlib import Path
from typing import Any

from clisops.config import get_config as _get_clisops_config
from clisops.config import reload_config as _reload_clisops_config


_PACKAGE_FILE = Path(__file__)
_CONFIG = _get_clisops_config(_PACKAGE_FILE)


class ConfigurationError(ValueError):
    """Raised when Rook configuration contains an invalid value."""


def get_config() -> dict[str, Any]:
    """Return the current Rook configuration."""
    return _CONFIG


def reload_config() -> dict[str, Any]:
    """Reload Rook configuration from the standard clisops sources."""
    global _CONFIG

    _CONFIG = _reload_clisops_config(_PACKAGE_FILE)
    return _CONFIG


def get_project_config(project: str) -> dict[str, Any]:
    """Return configuration for a project, or an empty mapping."""
    return _get_section(f"project:{project}")


def get_s3_storage_options() -> dict[str, Any]:
    """Build shared fsspec S3 transport options from Rook configuration."""
    config = _get_section("s3")

    options: dict[str, Any] = {}

    raw_options = config.get("storage_options_json")
    if raw_options:
        options.update(_parse_json_dict(raw_options, "storage_options_json"))

    if "anon" in options:
        options["anon"] = _parse_bool(options["anon"], "storage_options_json.anon")
    if "client_kwargs" in options and not isinstance(options["client_kwargs"], dict):
        raise ConfigurationError(
            "S3 option 'storage_options_json.client_kwargs' must be an object."
        )

    raw_client = config.get("client_kwargs_json")
    if raw_client:
        client_options = _parse_json_dict(raw_client, "client_kwargs_json")
        if client_options:
            _get_client_kwargs(options).update(client_options)

    endpoint_url = config.get("endpoint_url")
    if endpoint_url:
        _get_client_kwargs(options)["endpoint_url"] = endpoint_url

    for key in ("anon", "key", "secret", "token"):
        value = config.get(key)
        if value is None or value == "":
            continue
        options[key] = _parse_bool(value, "anon") if key == "anon" else value

    return options


def get_storage_base(project: str) -> str | None:
    """Return the preferred processing root for a project."""
    project_config = get_project_config(project)
    s3_config = _get_section("s3")
    global_s3_base = s3_config.get("base_dir")
    return (
        project_config.get("s3_base_dir")
        or global_s3_base
        or project_config.get("base_dir")
    )


def _get_section(name: str) -> dict[str, Any]:
    section = get_config().get(name, {})
    if not isinstance(section, dict):
        raise ConfigurationError(f"Configuration section [{name}] must be a mapping.")
    return section


def _get_client_kwargs(options: dict[str, Any]) -> dict[str, Any]:
    client_kwargs = options.setdefault("client_kwargs", {})
    if not isinstance(client_kwargs, dict):
        raise ConfigurationError("S3 option 'client_kwargs' must be an object.")
    return client_kwargs


def _parse_json_dict(value: Any, option: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        raise ConfigurationError(f"S3 option '{option}' must be a valid JSON object.") from None
    if not isinstance(parsed, dict):
        raise ConfigurationError(f"S3 option '{option}' must be a JSON object.")
    return parsed


def _parse_bool(value: Any, option: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    raise ConfigurationError(f"S3 option '{option}' must be a boolean.")
