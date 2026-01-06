import collections

import numpy as np
import xarray as xr

from clisops.parameter import collection_parameter
from clisops.parameter import dimension_parameter
from clisops.parameter import time_parameter
from clisops.parameter import time_components_parameter

from clisops.project_utils import derive_ds_id
from clisops.utils.dataset_utils import open_xr_dataset

from clisops.ops import subset
from clisops.core.average import average_over_dims as average

from daops.ops.base import Operation
from daops.utils import normalise

from .decadal_fixes import apply_decadal_fixes, decadal_fix_calendar
from .input_utils import fix_parameters

coord_by_standard_name = {
    "realization": "realization",
}


def drop_time_bnds(ds: xr.Dataset) -> xr.Dataset:
    """
    Drop time_bnds to avoid xarray CF encoding failures
    with dask + datetime objects.
    """
    if "time_bnds" in ds.variables:
        ds = ds.drop_vars("time_bnds")
    return ds


def patched_normalise(collection):
    # TODO: this is a patched function of daops to fix the gregorian calendar issue
    norm_collection = collections.OrderedDict()

    for dset, file_paths in collection.items():
        fixed_datasets = [
            decadal_fix_calendar(None, open_xr_dataset(file)) for file in file_paths
        ]
        ds = xr.concat(fixed_datasets, dim="time")
        # ds = xr.merge(fixed_datasets)
        norm_collection[dset] = ds

    return norm_collection


class Concat(Operation):
    def _resolve_params(self, collection, **params):
        """
        Resolve the input parameters to `self.params`.

        Parameterise the collection parameter and set it to `self.collection`.
        """
        time = time_parameter.TimeParameter(params.get("time"))
        time_components = time_components_parameter.TimeComponentsParameter(
            params.get("time_components")
        )
        dims = dimension_parameter.DimensionParameter(params.get("dims"))
        collection = collection_parameter.CollectionParameter(collection)

        self.collection = collection
        self.params = {
            "time": time,
            "time_components": time_components,
            "dims": dims,
            "apply_average": params.get("apply_average", False),
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
        norm_collection = patched_normalise(new_collection)

        rs = normalise.ResultSet(vars())

        # datasets = list(norm_collection.values())
        # apply decadal fixes
        datasets = []
        for ds_id in norm_collection.keys():
            ds = norm_collection[ds_id]
            ds_mod = apply_decadal_fixes(
                ds_id, ds, output_dir=self.params.get("output_dir", ".")
            )
            datasets.append(ds_mod)

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
        # optional: average
        if self.params.get("apply_average", False):
            processed_ds = average(processed_ds, dims=[dim])
            processed_ds = drop_time_bnds(processed_ds)
        # subset
        outputs = subset(
            processed_ds,
            time=self.params.get("time", None),
            time_components=self.params.get("time_components", None),
            output_type="nc",
        )
        # result
        rs.add("output", outputs)

        return rs


def _concat(
    collection,
    time=None,
    time_components=None,
    dims=None,
    ignore_undetected_dims=False,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
    apply_fixes=True,
    apply_average=False,
):
    result_set = Concat(**locals())._calculate()
    return result_set


def run_concat(args):
    args = fix_parameters(args)

    result = concat(**args)
    return result.file_uris


def concat(
    collection,
    time=None,
    time_components=None,
    dims=None,
    ignore_undetected_dims=False,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
    apply_fixes=True,
    apply_average=False,
):
    args = dict(
        collection=collection,
        time=time,
        time_components=time_components,
        dims=dims,
        ignore_undetected_dims=ignore_undetected_dims,
        output_dir=output_dir,
        output_type=output_type,
        split_method=split_method,
        file_namer=file_namer,
        apply_fixes=apply_fixes,
        apply_average=apply_average,
    )
    return _concat(**args)
