import collections

import numpy as np
import xarray as xr

from clisops.core.average import average_over_dims as average
from clisops.ops import subset
from clisops.parameter import collection_parameter
from clisops.parameter import dimension_parameter
from clisops.parameter import time_components_parameter
from clisops.parameter import time_parameter
from clisops.project_utils import derive_ds_id
from clisops.utils.dataset_utils import open_xr_dataset

from rook.utils.decadal_fixes import apply_decadal_fixes, decadal_fix_calendar

from . import normalise
from .base import Operation

coord_by_standard_name = {
    "realization": "realization",
}


def drop_time_bnds(ds: xr.Dataset) -> xr.Dataset:
    if "time_bnds" in ds.variables:
        ds = ds.drop_vars("time_bnds")
    return ds


def patched_normalise(collection):
    norm_collection = collections.OrderedDict()

    for dset, file_paths in collection.items():
        fixed_datasets = [
            decadal_fix_calendar(None, open_xr_dataset(file)) for file in file_paths
        ]
        ds = xr.concat(fixed_datasets, dim="time")
        norm_collection[dset] = ds

    return norm_collection


class Concat(Operation):
    def _resolve_params(self, collection, **params):
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

        for source in self.collection:
            ds_id = source.dataset_id or derive_ds_id(source.paths[0])
            new_collection[ds_id] = source.paths

        norm_collection = patched_normalise(new_collection)

        rs = normalise.ResultSet(vars())

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
        processed_ds = drop_time_bnds(processed_ds)
        if self.params.get("apply_average", False):
            processed_ds = average(processed_ds, dims=[dim])
        outputs = subset(
            processed_ds,
            time=self.params.get("time", None),
            time_components=self.params.get("time_components", None),
            output_type="nc",
        )
        rs.add("output", outputs)

        return rs


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
    apply_average=False,
):
    return Concat(
        collection=collection,
        time=time,
        time_components=time_components,
        dims=dims,
        ignore_undetected_dims=ignore_undetected_dims,
        output_dir=output_dir,
        output_type=output_type,
        split_method=split_method,
        file_namer=file_namer,
        apply_average=apply_average,
    )._calculate()
