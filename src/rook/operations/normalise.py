"""Normalise datasets and hold operation results."""

from collections import OrderedDict
import pathlib

from clisops.utils.dataset_utils import open_xr_dataset
from loguru import logger
import xarray as xr

from rook.diagnostics import dataset_signature, dataset_summary, memory_checkpoint
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
        memory_checkpoint(
            "normalise group start",
            f"group={dset} files={len(file_paths)}",
        )
        datasets = []
        for index, file in enumerate(file_paths, start=1):
            file_label = f"group={dset} file={index}/{len(file_paths)}"
            memory_checkpoint("before opening file", file_label)
            dataset = opener(file)
            memory_checkpoint(
                "after opening file",
                f"{file_label} {dataset_summary(dataset)}",
            )
            memory_checkpoint("before prepare_dataset", file_label)
            dataset = prepare_dataset(dataset)
            memory_checkpoint(
                "after prepare_dataset",
                f"{file_label} {dataset_summary(dataset)}",
            )
            datasets.append(dataset)

        memory_checkpoint("before normalise xr.concat", f"group={dset}")
        normalized = xr.concat(
            datasets,
            dim=concat_dim,
            data_vars="minimal",
            coords="minimal",
            compat="override",
            join="exact",
        )
        norm_collection[dset] = normalized
        memory_checkpoint(
            "after normalise xr.concat",
            f"group={dset} {dataset_summary(normalized)}",
        )
        dataset_signature("after normalized group concat", normalized, identity=dset)

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
            if isinstance(item, str) and (
                pathlib.Path(item).is_file() or item.startswith("https")
            ):
                self.file_uris.append(item)
