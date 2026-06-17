"""Helper utilities for operation plumbing."""

import collections
from pathlib import Path
from urllib.parse import urlsplit

from clisops.utils.dataset_utils import open_xr_dataset

from rook.utils.apply_fixes import apply_fixes as apply_dataset_fixes

KERCHUNK_EXTS = (".json", ".zst", ".zstd", ".parquet")


def wrap_sequence(obj):
    """Return a list for scalar inputs and preserve sequences."""
    if isinstance(obj, str):
        obj = [obj]
    return obj


def open_dataset(ds_id, file_paths, apply_fixes=True):
    """Open an xarray Dataset and optionally apply rook-native fixes."""
    ds = open_xr_dataset(file_paths)

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
