"""Utilities for detecting and opening supported datasets."""

from pathlib import Path
from urllib.parse import urlsplit

import xarray as xr
from clisops.utils.dataset_utils import open_xr_dataset

from rook import config
from rook.utils.apply_fixes import apply_fixes as apply_dataset_fixes

KERCHUNK_EXTS = (".json", ".zst", ".zstd", ".parquet")
ZARR_EXT = ".zarr"


def open_dataset(ds_id, file_paths, apply_fixes=True):
    """Open an xarray Dataset and optionally apply rook-native fixes."""
    zarr_store = get_zarr_store(ds_id, file_paths)
    if zarr_store:
        ds = xr.open_zarr(zarr_store, **get_zarr_open_kwargs(zarr_store))
    else:
        open_kwargs = get_s3_open_kwargs(ds_id, file_paths)
        ds = open_xr_dataset(file_paths, **open_kwargs)

    if apply_fixes and not is_kerchunk_file(ds_id) and not is_zarr_store(ds_id):
        ds = apply_dataset_fixes(ds_id, ds)

    return ds


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


def is_zarr_store(dset):
    """Return True when the input looks like a Zarr store path."""
    if isinstance(dset, Path):
        dset = str(dset)

    if not isinstance(dset, str):
        return False

    value = dset.strip()
    if not value:
        return False

    path = urlsplit(value).path.rstrip("/").lower()
    return path.endswith(ZARR_EXT)


def get_zarr_store(ds_id, file_paths):
    """Return a single Zarr store from a dataset id or resolved file paths."""
    if is_zarr_store(ds_id):
        return str(ds_id)

    if isinstance(file_paths, (str, Path)):
        return str(file_paths) if is_zarr_store(file_paths) else None

    if file_paths and len(file_paths) == 1 and is_zarr_store(file_paths[0]):
        return str(file_paths[0])

    return None


def get_zarr_open_kwargs(store):
    """Return xarray opener kwargs for a Zarr store."""
    if not is_s3_uri(store):
        return {}

    storage_options = get_s3_storage_options()
    if not storage_options:
        return {}

    return {"storage_options": storage_options}


def get_s3_open_kwargs(ds_id, file_paths):
    """Return opener kwargs for S3-hosted NetCDF inputs."""
    dset = ds_id
    if not isinstance(dset, str) and file_paths:
        dset = str(file_paths[0])

    if not is_s3_uri(dset) or is_kerchunk_file(dset) or is_zarr_store(dset):
        return {}

    storage_options = get_s3_storage_options()
    if not storage_options:
        return {}

    return {"backend_kwargs": {"storage_options": storage_options}}


def get_s3_storage_options():
    """Return shared S3 transport options from central configuration."""
    return config.get_s3_storage_options()
