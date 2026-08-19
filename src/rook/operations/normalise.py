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


def open_lazy_xr_dataset(path):
    """Open one grouped file with Dask-backed, storage-aware chunks."""
    return open_xr_dataset(str(path), chunks={})


def normalise_file_groups(
    collection,
    *,
    prepare_dataset=None,
    concat_dim="time",
    opener=open_lazy_xr_dataset,
):
    """Open grouped file paths and concatenate each group."""
    norm_collection = OrderedDict()

    if prepare_dataset is None:
        prepare_dataset = keep_dataset

    for dset, file_paths in collection.items():
        file_paths = tuple(file_paths)
        datasets = []
        opened_datasets = []
        try:
            for file in file_paths:
                opened = opener(file)
                opened_datasets.append(opened)
                dataset = prepare_dataset(opened)
                datasets.append(dataset)

            normalized = xr.concat(
                datasets,
                dim=concat_dim,
                data_vars="minimal",
                coords="minimal",
                compat="override",
                join="exact",
            )
        except Exception:
            _close_datasets(datasets, opened_datasets)
            raise

        normalized.set_close(
            lambda datasets=datasets, opened=opened_datasets: _close_datasets(
                datasets, opened
            )
        )
        norm_collection[dset] = normalized

    return norm_collection


def _close_datasets(*groups):
    """Close datasets once, preserving all lazy inputs until group close."""
    closed = set()
    for datasets in groups:
        for dataset in datasets:
            identity = id(dataset)
            if identity not in closed:
                dataset.close()
                closed.add(identity)


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
            if isinstance(item, str) and (
                pathlib.Path(item).is_file() or item.startswith("https")
            ):
                self.file_uris.append(item)
