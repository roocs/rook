"""Subset operation with rook-specific fix application."""

from clisops.ops.subset import subset as clisops_subset
from clisops.parameter import parameterise

from rook.utils.apply_fixes import apply_fixes

from .base import Operation
from . import normalise

__all__ = ["Subset", "subset"]


class Subset(Operation):
    def _resolve_params(self, collection, **params):
        parameters = parameterise(
            collection=collection,
            time=params.get("time"),
            area=params.get("area"),
            level=params.get("level"),
            time_components=params.get("time_components"),
        )

        self.collection = parameters.pop("collection")
        self.params = parameters

    def calculate(self):
        config = {
            "output_type": self._output_type,
            "output_dir": self._output_dir,
            "split_method": self._split_method,
            "file_namer": self._file_namer,
        }

        self.params.update(config)

        norm_collection = normalise.normalise(self.collection, False)
        rs = normalise.ResultSet(vars())

        for dset, norm_collection_ in norm_collection.items():
            fixed_collection = apply_fixes(dset, norm_collection_)
            rs.add(dset, clisops_subset(fixed_collection, **self.params))

        return rs


def subset(
    collection,
    time=None,
    area=None,
    level=None,
    time_components=None,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
    apply_fixes=False,
):
    return Subset(**locals()).calculate()
