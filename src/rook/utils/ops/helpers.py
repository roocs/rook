"""Helper utilities for operation plumbing."""

import collections

from clisops.utils.dataset_utils import is_kerchunk_file, open_xr_dataset

from rook.utils.apply_fixes import apply_fixes as apply_dataset_fixes


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
