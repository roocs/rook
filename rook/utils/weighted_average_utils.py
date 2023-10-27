from roocs_utils.parameter import collection_parameter
from roocs_utils.parameter import dimension_parameter

from daops.ops.base import Operation

from clisops.ops import average_over_dims

class WeightedAverage(Operation):
    def _resolve_params(self, collection, **params):
        """
        Resolve the input parameters to `self.params` and parameterise
        collection parameter and set to `self.collection`.
        """
        dims = dimension_parameter.DimensionParameter(params.get("dims"))
        collection = collection_parameter.CollectionParameter(collection)

        self.collection = collection
        self.params = {
            "dims": dims,
            "ignore_undetected_dims": params.get("ignore_undetected_dims"),
        }

    # def get_operation_callable(self):
    #     return clisops_average_over_dims

    def _calculate(self):
        avg_ds = average_over_dims(
            self.ds,
            self.params.get("dims", None),
            self.params.get("ignore_undetected_dims", None),
        )

        return avg_ds