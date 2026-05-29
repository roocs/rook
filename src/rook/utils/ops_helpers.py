"""Helper utilities for operation plumbing."""

import collections

from clisops.utils.dataset_utils import is_kerchunk_file, open_xr_dataset
from loguru import logger


def wrap_sequence(obj):
    """Return a list for scalar inputs and preserve sequences."""
    if isinstance(obj, str):
        obj = [obj]
    return obj


def open_dataset(ds_id, file_paths, apply_fixes=True):
    """Open an xarray Dataset and optionally apply daops fixes if available."""
    if apply_fixes and not is_kerchunk_file(ds_id):
        try:
            from daops.utils import fixer

            fix = fixer.Fixer(ds_id)
            if fix.pre_processor:
                for pre_process in fix.pre_processors:
                    logger.info(f"Loading data with pre_processor: {pre_process.__name__}")
            else:
                logger.info("Loading data")

            ds = open_xr_dataset(file_paths, preprocess=fix.pre_processor)

            if fix.post_processors:
                for post_process in fix.post_processors:
                    func, operands = post_process
                    logger.info(
                        f"Running post-processing function: {func.__name__}"
                    )
                    ds = func(ds_id, ds, **operands)
            return ds
        except Exception:
            # Fall back to plain dataset open when daops fixer path is unavailable.
            pass

    return open_xr_dataset(file_paths)


def ordered_dict():
    """Return an OrderedDict instance."""
    return collections.OrderedDict()
