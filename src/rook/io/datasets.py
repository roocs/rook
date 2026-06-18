"""Utilities for detecting and opening supported datasets."""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import xarray as xr
from clisops.utils.dataset_utils import open_xr_dataset

from rook import config
from rook.utils.apply_fixes import apply_fixes as apply_dataset_fixes

KERCHUNK_EXTS = (".json", ".zst", ".zstd", ".parquet")
ZARR_EXT = ".zarr"


@dataclass(frozen=True, init=False)
class DatasetSource:
    """A normalized set of paths and its optional catalog dataset id."""

    dataset_id: str | None
    paths: tuple[str, ...]

    def __init__(
        self,
        dataset_id: str | None,
        paths: str | Path | Iterable[str | Path],
    ):
        """Normalize and validate source paths."""
        if isinstance(paths, (str, Path)):
            paths = (str(paths),)
        else:
            paths = tuple(str(path) for path in paths)

        if not paths:
            raise ValueError("A dataset source requires at least one path.")
        if len(paths) > 1 and any(
            is_kerchunk_file(path) or is_zarr_store(path) for path in paths
        ):
            raise ValueError("Zarr and Kerchunk sources require exactly one path.")

        if dataset_id is not None:
            dataset_id = str(dataset_id)
        object.__setattr__(self, "dataset_id", dataset_id)
        object.__setattr__(self, "paths", paths)

    @property
    def key(self):
        """Return the identifier used for operation result mappings."""
        return self.dataset_id or self.paths[0]


def open_dataset(source: DatasetSource, *, apply_fixes=True):
    """Open an xarray Dataset and optionally apply rook-native fixes."""
    zarr_store = get_zarr_store(source)
    if zarr_store:
        ds = xr.open_zarr(zarr_store, **get_zarr_open_kwargs(zarr_store))
    else:
        open_kwargs = get_s3_open_kwargs(source)
        paths = source.paths[0] if is_kerchunk_file(source.paths[0]) else list(source.paths)
        ds = open_xr_dataset(paths, **open_kwargs)

    if apply_fixes and source.dataset_id:
        ds = apply_dataset_fixes(source.dataset_id, ds)

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


def get_zarr_store(source: DatasetSource):
    """Return the store path when a source contains exactly one Zarr store."""
    if len(source.paths) == 1 and is_zarr_store(source.paths[0]):
        return source.paths[0]

    return None


def get_zarr_open_kwargs(store):
    """Return xarray opener kwargs for a Zarr store."""
    if not is_s3_uri(store):
        return {}

    storage_options = get_s3_storage_options()
    if not storage_options:
        return {}

    return {"storage_options": storage_options}


def get_s3_open_kwargs(source: DatasetSource):
    """Return opener kwargs for S3-hosted NetCDF inputs."""
    dset = source.paths[0]

    if not is_s3_uri(dset) or is_kerchunk_file(dset) or is_zarr_store(dset):
        return {}

    storage_options = get_s3_storage_options()
    if not storage_options:
        return {}

    return {"backend_kwargs": {"storage_options": storage_options}}


def get_s3_storage_options():
    """Return shared S3 transport options from central configuration."""
    return config.get_s3_storage_options()
