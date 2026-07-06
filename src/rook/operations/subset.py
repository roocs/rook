"""Subset operation."""

from clisops.ops.subset import subset as clisops_subset
from clisops.parameter import (
    area_parameter,
    level_parameter,
    time_components_parameter,
    time_parameter,
)

from .base import Operation, resolve_collection
from . import normalise

__all__ = ["Subset", "subset"]


class Subset(Operation):
    def _resolve_params(self, collection, **params):
        self.collection = resolve_collection(collection)
        self.params = {
            "area": area_parameter.AreaParameter(params.get("area")),
            "level": level_parameter.LevelParameter(params.get("level")),
            "time": time_parameter.TimeParameter(params.get("time")),
            "time_components": time_components_parameter.TimeComponentsParameter(
                params.get("time_components")
            ),
        }

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

        for dset, dataset in norm_collection.items():
            rs.add(dset, clisops_subset(dataset, **self.params))

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
):
    return Subset(**locals()).calculate()
