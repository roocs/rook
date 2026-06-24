"""Utilities for detecting and opening supported datasets."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from urllib.parse import urlsplit

import xarray as xr
from clisops.utils.dataset_utils import open_xr_dataset

from rook import config
from rook.utils.apply_fixes import apply_fixes as apply_dataset_fixes

KERCHUNK_EXTS = (".json", ".zst", ".zstd", ".parquet")
ZARR_EXT = ".zarr"


class DatasetFormat(Enum):
    """Dataset formats supported by Rook."""

    NETCDF = "netcdf"
    ZARR = "zarr"
    KERCHUNK = "kerchunk"


class Transport(Enum):
    """Transport protocols relevant to dataset opening."""

    FILESYSTEM = "filesystem"
    HTTP = "http"
    S3 = "s3"
    REFERENCE = "reference"
    OTHER = "other"


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


def detect_format(source: DatasetSource) -> DatasetFormat:
    """Detect the data format independently of its transport protocol."""
    path = source.paths[0]
    if is_zarr_store(path):
        return DatasetFormat.ZARR
    if is_kerchunk_file(path):
        return DatasetFormat.KERCHUNK
    return DatasetFormat.NETCDF


def detect_transport(source: DatasetSource) -> Transport:
    """Detect and validate the transport shared by all source paths."""
    transports = {_detect_path_transport(path) for path in source.paths}
    if len(transports) != 1:
        names = ", ".join(sorted(transport.value for transport in transports))
        raise ValueError(f"Dataset paths use mixed transports: {names}.")
    return transports.pop()


def get_storage_options(source: DatasetSource) -> dict:
    """Return transport options for a dataset source."""
    if detect_transport(source) is Transport.S3:
        return config.get_s3_storage_options()
    return {}


def open_netcdf(source: DatasetSource, storage_options: dict):
    """Open one or more NetCDF files through the established clisops opener."""
    kwargs = {}
    if storage_options:
        kwargs["backend_kwargs"] = {"storage_options": storage_options}
    return open_xr_dataset(list(source.paths), **kwargs)


def open_zarr(source: DatasetSource, storage_options: dict):
    """Open a single Zarr store."""
    kwargs = {"storage_options": storage_options} if storage_options else {}
    return xr.open_zarr(source.paths[0], **kwargs)


def open_kerchunk(source: DatasetSource, storage_options: dict):
    """Open a single Kerchunk reference through the established clisops path."""
    kwargs = {"target_options": storage_options} if storage_options else {}
    return open_xr_dataset(source.paths[0], **kwargs)


_OPENERS = {
    DatasetFormat.NETCDF: open_netcdf,
    DatasetFormat.ZARR: open_zarr,
    DatasetFormat.KERCHUNK: open_kerchunk,
}


def open_dataset(source: DatasetSource):
    """Open an xarray Dataset and apply catalog-specific fixes when available."""
    opener = _OPENERS[detect_format(source)]
    ds = opener(source, get_storage_options(source))

    if source.dataset_id:
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


def _detect_path_transport(path: str) -> Transport:
    scheme = urlsplit(path.strip()).scheme.lower()
    if scheme in {"", "file"}:
        return Transport.FILESYSTEM
    if scheme in {"http", "https"}:
        return Transport.HTTP
    if scheme == "s3":
        return Transport.S3
    if scheme == "reference":
        return Transport.REFERENCE
    return Transport.OTHER
