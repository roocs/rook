"""Normalise datasets and hold operation results."""

import pathlib

from loguru import logger

from rook.io.datasets import open_dataset

from .helpers import ordered_dict


def normalise(collection, apply_fixes=True):
    """Open input collections and apply fixes when requested."""
    logger.info(f"Working on datasets: {collection}")
    norm_collection = ordered_dict()

    for source in collection:
        ds = open_dataset(source, apply_fixes=apply_fixes)
        norm_collection[source.key] = ds

    return norm_collection


class ResultSet:
    """A class to hold the results from an operation."""

    def __init__(self, inputs=None):  # noqa: D107
        self._results = ordered_dict()
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
