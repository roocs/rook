"""Subset operation."""

from clisops.ops.subset import subset as clisops_subset
from clisops.parameter import (
    area_parameter,
    level_parameter,
    time_components_parameter,
    time_parameter,
)

from .base import Operation, resolve_collection

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
            "fix_provider": params.get("fix_provider"),
        }

    def get_operation_callable(self):
        return clisops_subset


def subset(
    collection,
    time=None,
    area=None,
    level=None,
    time_components=None,
    fix_provider=None,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
):
    return Subset(**locals()).calculate()
