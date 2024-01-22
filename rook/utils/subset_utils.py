from .input_utils import fix_parameters
from .apply_fixes import apply_fixes

from clisops.ops.subset import subset as clisops_subset
from roocs_utils.parameter import parameterise
from roocs_utils.project_utils import derive_ds_id

from daops.ops.base import Operation
from daops.utils import normalise


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

        # Normalise data inputs based
        norm_collection = normalise.normalise(self.collection, False)

        rs = normalise.ResultSet(vars())

        for dset, norm_collection in norm_collection.items():
            ds_id = derive_ds_id(dset)
            fixed_collection = apply_fixes(ds_id, norm_collection)
            if "atlas" in ds_id:
                self.params["file_namer"] = "simple"
            rs.add(
                dset,
                clisops_subset(fixed_collection, **self.params),
            )

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
    result_set = Subset(**locals()).calculate()

    return result_set


def run_subset(args):
    args = fix_parameters(args)

    result = subset(**args)
    return result.file_uris
