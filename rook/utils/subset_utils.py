from .input_utils import fix_parameters

from clisops.ops.subset import subset as clisops_subset
from roocs_utils.parameter import parameterise

from daops.ops.base import Operation


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

    def get_operation_callable(self):
        return clisops_subset


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
    apply_fixes=True,
):
    result_set = Subset(**locals()).calculate()

    return result_set


def run_subset(args):
    args = fix_parameters(args)

    result = subset(**args)
    return result.file_uris
