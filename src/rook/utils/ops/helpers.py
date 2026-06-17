"""Helper utilities for operation plumbing."""

import collections
import json
from pathlib import Path
from urllib.parse import urlsplit

from clisops.utils.dataset_utils import open_xr_dataset

from rook import CONFIG
from rook.utils.apply_fixes import apply_fixes as apply_dataset_fixes

KERCHUNK_EXTS = (".json", ".zst", ".zstd", ".parquet")


def wrap_sequence(obj):
    """Return a list for scalar inputs and preserve sequences."""
    if isinstance(obj, str):
        obj = [obj]
    return obj


def open_dataset(ds_id, file_paths, apply_fixes=True):
    """Open an xarray Dataset and optionally apply rook-native fixes."""
    open_kwargs = get_s3_open_kwargs(ds_id, file_paths)
    ds = open_xr_dataset(file_paths, **open_kwargs)

    if apply_fixes and not is_kerchunk_file(ds_id):
        ds = apply_dataset_fixes(ds_id, ds)

    return ds


def ordered_dict():
    """Return an OrderedDict instance."""
    return collections.OrderedDict()


def is_kerchunk_file(dset):
    # Keep this local detector in sync with clisops and upstream when possible.
    # Rook currently needs URL-aware kerchunk detection before clisops changes land.
    """Return True when the input looks like a kerchunk reference file."""
    if isinstance(dset, Path):
        dset = str(dset)

    if not isinstance(dset, str):
        return False

    value = dset.strip()
    if not value:
        return False

    if value.lower().startswith("reference://"):
        return True

    # Support local paths and URLs, including query fragments.
    path = urlsplit(value).path.lower()
    return path.endswith(KERCHUNK_EXTS)


def is_s3_uri(dset):
    """Return True when the input points to an S3 object URI."""
    if isinstance(dset, Path):
        dset = str(dset)

    if not isinstance(dset, str):
        return False

    value = dset.strip()
    if not value:
        return False

    return value.lower().startswith("s3://")


def get_s3_open_kwargs(ds_id, file_paths):
    """Return opener kwargs for S3-hosted NetCDF inputs."""
    dset = ds_id
    if not isinstance(dset, str) and file_paths:
        dset = str(file_paths[0])

    if not is_s3_uri(dset) or is_kerchunk_file(dset):
        return {}

    storage_options = get_s3_storage_options()
    if not storage_options:
        return {}

    return {"backend_kwargs": {"storage_options": storage_options}}


def get_s3_storage_options():
    """Build fsspec S3 storage options from rook config."""
    cfg = CONFIG.get("s3", {})
    if not isinstance(cfg, dict):
        return {}

    options = {}

    raw_options = cfg.get("storage_options_json")
    if raw_options:
        parsed = _parse_json_dict(raw_options)
        if parsed:
            options.update(parsed)

    raw_client = cfg.get("client_kwargs_json")
    if raw_client:
        parsed = _parse_json_dict(raw_client)
        if parsed:
            options["client_kwargs"] = parsed

    endpoint_url = cfg.get("endpoint_url")
    if endpoint_url:
        options.setdefault("client_kwargs", {})["endpoint_url"] = endpoint_url

    for key in ("anon", "key", "secret", "token"):
        value = cfg.get(key)
        if value is None or value == "":
            continue
        if key == "anon":
            value = _coerce_bool(value)
        options[key] = value

    return options


def _parse_json_dict(value):
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _coerce_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return value
