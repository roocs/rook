"""Normalise datasets and hold operation results."""

from collections import OrderedDict
import pathlib

from clisops.utils.dataset_utils import open_xr_dataset
from loguru import logger
import xarray as xr

from rook.io.datasets import open_dataset


def normalise(collection):
    """Open input collections."""
    logger.info(f"Working on datasets: {collection}")
    norm_collection = OrderedDict()

    for source in collection:
        ds = open_dataset(source)
        norm_collection[source.key] = ds

    return norm_collection


def keep_dataset(ds):
    """Return a dataset unchanged."""
    return ds


def normalise_file_groups(
    collection,
    *,
    prepare_dataset=None,
    concat_dim="time",
    opener=open_xr_dataset,
):
    """Open grouped file paths and concatenate each group."""
    norm_collection = OrderedDict()

    if prepare_dataset is None:
        prepare_dataset = keep_dataset

    for dset, file_paths in collection.items():
        datasets = [prepare_dataset(opener(file)) for file in file_paths]
        norm_collection[dset] = xr.concat(datasets, dim=concat_dim)

    return norm_collection


class ResultSet:
    """A class to hold the results from an operation."""

    def __init__(self, inputs=None):  # noqa: D107
        self._results = OrderedDict()
        self.metadata = {"inputs": inputs, "process": "something", "version": 0.1}
        self.file_uris = []

    def add(self, dset, result):
        """Add outputs with ds id key and collect file URIs."""
        self._results[dset] = result

        for item in result:
            if isinstance(item, str) and (pathlib.Path(item).is_file() or item.startswith("https")):
                self.file_uris.append(item)
