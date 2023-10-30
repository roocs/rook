# import numpy as np
# import xarray as xr

from roocs_utils.parameter import collection_parameter
from roocs_utils.parameter import dimension_parameter


from daops.ops.base import Operation

from clisops.ops.average import average_over_dims as clisops_average_over_dims


class WeightedAverage(Operation):
    def _resolve_params(self, collection, **params):
        """
        Resolve the input parameters to `self.params` and parameterise
        collection parameter and set to `self.collection`.
        """
        dims = dimension_parameter.DimensionParameter(["latitude", "longitude"])
        collection = collection_parameter.CollectionParameter(collection)

        self.collection = collection
        self.params = {
            "dims": dims,
            "ignore_undetected_dims": params.get("ignore_undetected_dims"),
        }

    def get_operation_callable(self):
        return clisops_average_over_dims

    
def run_weighted_average(args):
    result = weighted_average(**args)
    return result.file_uris


def weighted_average(
    collection,
    ignore_undetected_dims=False,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
    apply_fixes=False,
    apply_average=False,
):
    result_set = WeightedAverage(**locals()).calculate()
    return result_set