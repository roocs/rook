"""Normalise datasets and hold operation results."""

from collections import OrderedDict
import pathlib

from loguru import logger

from rook.io.datasets import open_dataset


def normalise(collection):
    """Open input collections."""
    logger.info(f"Working on datasets: {collection}")
    norm_collection = OrderedDict()

    for source in collection:
        ds = open_dataset(source)
        norm_collection[source.key] = ds

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
