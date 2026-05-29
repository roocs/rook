"""Operations for averaging data over dimensions, shape or time."""

from clisops.ops.average import average_over_dims as clisops_average_over_dims
from clisops.ops.average import average_shape as clisops_average_shape
from clisops.ops.average import average_time as clisops_average_time
from clisops.parameter import collection_parameter, dimension_parameter

from .base_selector import get_operation_base

Operation = get_operation_base(default_local=True)

__all__ = ["average_over_dims", "average_shape", "average_time", "Average"]


class Average(Operation):
    def _resolve_params(self, collection, **params):
        dims = dimension_parameter.DimensionParameter(params.get("dims"))
        collection = collection_parameter.CollectionParameter(collection)

        self.collection = collection
        self.params = {
            "dims": dims,
            "ignore_undetected_dims": params.get("ignore_undetected_dims"),
        }

    def get_operation_callable(self):
        return clisops_average_over_dims


def average_over_dims(
    collection,
    dims=None,
    ignore_undetected_dims=False,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
    apply_fixes=True,
):
    return Average(**locals()).calculate()


class AverageShape(Operation):
    def _resolve_params(self, collection, **params):
        shape = params.get("shape")
        collection = collection_parameter.CollectionParameter(collection)

        self.collection = collection
        self.params = {
            "shape": shape,
            "variable": params.get("variable"),
        }

    def get_operation_callable(self):
        return clisops_average_shape


def average_shape(
    collection,
    shape,
    variable=None,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
    apply_fixes=True,
):
    return AverageShape(**locals()).calculate()


class AverageTime(Operation):
    def _resolve_params(self, collection, **params):
        freq = params.get("freq")
        collection = collection_parameter.CollectionParameter(collection)

        self.collection = collection
        self.params = {
            "freq": freq,
        }

    def get_operation_callable(self):
        return clisops_average_time


def average_time(
    collection,
    freq="year",
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
    apply_fixes=True,
):
    return AverageTime(**locals()).calculate()