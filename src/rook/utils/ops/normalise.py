"""Normalise datasets and hold operation results."""

import os

from loguru import logger

from .helpers import open_dataset, ordered_dict


def normalise(collection, apply_fixes=True):
    """Open input collections and apply fixes when requested."""
    logger.info(f"Working on datasets: {collection}")
    norm_collection = ordered_dict()

    for dset, file_paths in collection.items():
        ds = open_dataset(dset, file_paths, apply_fixes)
        norm_collection[dset] = ds

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
                os.path.isfile(item) or item.startswith("https")
            ):
                self.file_uris.append(item)
