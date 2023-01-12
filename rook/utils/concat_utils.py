import xarray as xr

from roocs_utils.parameter import collection_parameter

from daops.ops.base import Operation
from daops.utils import normalise


class Concat(Operation):
    def _resolve_params(self, collection, **params):
        """
        Resolve the input parameters to `self.params` and parameterise
        collection parameter and set to `self.collection`.
        """
        collection = collection_parameter.CollectionParameter(collection)

        self.collection = collection
        self.params = {
            "ignore_undetected_dims": params.get("ignore_undetected_dims"),
        }

    def _calculate(self):
        config = {
            "output_type": self._output_type,
            "output_dir": self._output_dir,
            "split_method": self._split_method,
            "file_namer": self._file_namer,
        }

        self.params.update(config)

        # Normalise (i.e. "fix") data inputs based on "character"
        norm_collection = normalise.normalise(self.collection, self._apply_fixes)

        rs = normalise.ResultSet(vars())

        dset = list(norm_collection.keys())[0]
        datasets = list(norm_collection.values())

        result = xr.concat(datasets, dim="realization").mean(dim="realization")
        raise Exception(result)

        rs.add(dset, result)

        return rs


def _concat(
    collection,
    dims=None,
    ignore_undetected_dims=False,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
    apply_fixes=True,
):
    result_set = Concat(**locals())._calculate()
    return result_set


def run_concat(args):
    result = concat(**args)
    return result.file_uris


def concat(
    collection,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
    apply_fixes=True,
):
    # dummy concat operator
    # from daops.ops.average import average_over_dims

    args = dict(
        collection=collection,
        output_dir=output_dir,
        output_type=output_type,
        split_method=split_method,
        file_namer=file_namer,
        apply_fixes=apply_fixes,
    )
    return _concat(**args)
