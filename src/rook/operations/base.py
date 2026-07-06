"""Base class for operation execution."""

from dataclasses import dataclass

from clisops.parameter import collection_parameter

from rook.io.datasets import DatasetSource

from . import consolidate, normalise
from .processor import process


@dataclass(frozen=True)
class PreparedCollection:
    """Collection wrapper for already-resolved dataset sources."""

    value: tuple[DatasetSource, ...]


class Operation:
    """Base class for all operations."""

    def __init__(
        self,
        collection,
        file_namer="standard",
        split_method="time:auto",
        output_dir=None,
        output_type="netcdf",
        **params,
    ):
        self._file_namer = file_namer
        self._split_method = split_method
        self._output_dir = output_dir
        self._output_type = output_type
        self._resolve_params(collection, **params)
        self._consolidate_collection()

    def _resolve_params(self, collection, **params):
        self.collection = resolve_collection(collection)
        self.params = params

    def _consolidate_collection(self):
        if "time" in self.params:
            self.collection = consolidate.consolidate(
                self.collection, time=self.params.get("time")
            )
        else:
            self.collection = consolidate.consolidate(self.collection)

    def get_operation_callable(self):
        raise NotImplementedError

    def calculate(self):
        config = {
            "output_type": self._output_type,
            "output_dir": self._output_dir,
            "split_method": self._split_method,
            "file_namer": self._file_namer,
        }

        self.params.update(config)

        norm_collection = normalise.normalise(self.collection)

        rs = normalise.ResultSet(vars())

        for dset, collection in norm_collection.items():
            rs.add(
                dset,
                process(self.get_operation_callable(), collection, **self.params),
            )

        return rs


def is_prepared_dataset_collection(collection):
    """Return whether a collection contains normalized dataset sources."""
    return bool(collection) and isinstance(collection, (list, tuple)) and all(
        isinstance(item, DatasetSource) for item in collection
    )


def resolve_collection(collection):
    """Return a collection value suitable for operation consolidation."""
    if is_prepared_dataset_collection(collection):
        return PreparedCollection(value=tuple(collection))
    return collection_parameter.CollectionParameter(collection)
