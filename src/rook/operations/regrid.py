"""Regrid operation."""

from clisops.ops.regrid import regrid as clisops_regrid
from clisops.parameter import collection_parameter

from .base import Operation

__all__ = ["Regrid", "regrid"]


class Regrid(Operation):
    def _resolve_params(self, collection, **params):
        collection = collection_parameter.CollectionParameter(collection)

        self.collection = collection
        self.params = {
            "method": params.get("method"),
            "adaptive_masking_threshold": params.get("adaptive_masking_threshold"),
            "grid": params.get("grid"),
        }

    def get_operation_callable(self):
        return clisops_regrid


def regrid(
    collection,
    method="nn",
    adaptive_masking_threshold=0.5,
    grid="1deg",
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
):
    return Regrid(**locals()).calculate()
