import xarray as xr
import numpy as np

import collections

from roocs_utils.parameter import collection_parameter
from roocs_utils.parameter import dimension_parameter

from roocs_utils.project_utils import derive_ds_id

from daops.ops.base import Operation
from daops.utils import normalise

from clisops.utils.file_namers import get_file_namer
from clisops.utils.output_utils import get_output, get_time_slices

coord_by_standard_name = {
    "realization": "realization_index",
}


class Concat(Operation):
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

    def _calculate(self):
        config = {
            "output_type": self._output_type,
            "output_dir": self._output_dir,
            "split_method": self._split_method,
            "file_namer": self._file_namer,
        }

        self.params.update(config)

        new_collection = collections.OrderedDict()

        for dset in self.collection:
            ds_id = derive_ds_id(dset)
            new_collection[ds_id] = dset.file_paths

        # Normalise (i.e. "fix") data inputs based on "character"
        norm_collection = normalise.normalise(new_collection, self._apply_fixes)

        rs = normalise.ResultSet(vars())

        datasets = list(norm_collection.values())

        dims = dimension_parameter.DimensionParameter(
            self.params.get("dims", None)
        ).value
        standard_name = dims[0]
        dim = coord_by_standard_name.get(standard_name, None)

        processed_ds = xr.concat(
            datasets,
            dim,
        )
        processed_ds = processed_ds.assign_coords(
            {dim: (dim, np.array(processed_ds[dim].values, dtype="int32"))}
        )
        processed_ds.coords[dim].attrs = {"standard_name": standard_name}

        namer = get_file_namer("standard")()
        time_slices = get_time_slices(processed_ds, "time:auto")

        outputs = list()
        # Loop through each time slice
        for tslice in time_slices:

            # If there is only one time slice, and it is None:
            # - then just set the result Dataset to the processed Dataset
            if tslice is None:
                result_ds = processed_ds
            # If there is a time slice then extract the time slice from the
            # processed Dataset
            else:
                result_ds = processed_ds.sel(time=slice(tslice[0], tslice[1]))

            # print(f"for times: {tslice}")

            # Get the output (file or xarray Dataset)
            # When this is a file: xarray will read all the data and write the file
            output = get_output(
                result_ds,
                output_type="nc",
                output_dir=self._output_dir,
                namer=namer,
            )
            outputs.append(output)

        rs.add("output", outputs)

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
    dims=None,
    ignore_undetected_dims=False,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
    apply_fixes=True,
):
    args = dict(
        collection=collection,
        dims=dims,
        ignore_undetected_dims=ignore_undetected_dims,
        output_dir=output_dir,
        output_type=output_type,
        split_method=split_method,
        file_namer=file_namer,
        apply_fixes=apply_fixes,
    )
    return _concat(**args)
