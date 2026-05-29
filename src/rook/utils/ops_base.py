"""Base class for operation execution."""

from clisops.parameter import collection_parameter

from . import ops_consolidate, ops_normalise
from .ops_processor import process


class Operation:
    """Base class for all operations."""

    def __init__(
        self,
        collection,
        file_namer="standard",
        split_method="time:auto",
        output_dir=None,
        output_type="netcdf",
        apply_fixes=True,
        **params,
    ):
        self._file_namer = file_namer
        self._split_method = split_method
        self._output_dir = output_dir
        self._output_type = output_type
        self._apply_fixes = apply_fixes
        self._resolve_params(collection, **params)
        self._consolidate_collection()

    def _resolve_params(self, collection, **params):
        self.collection = collection_parameter.CollectionParameter(collection)
        self.params = params

    def _consolidate_collection(self):
        if "time" in self.params:
            self.collection = ops_consolidate.consolidate(
                self.collection, time=self.params.get("time")
            )
        else:
            self.collection = ops_consolidate.consolidate(self.collection)

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

        norm_collection = ops_normalise.normalise(self.collection, self._apply_fixes)

        rs = ops_normalise.ResultSet(vars())

        for dset, collection in norm_collection.items():
            rs.add(
                dset,
                process(self.get_operation_callable(), collection, **self.params),
            )

        return rs
