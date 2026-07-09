import collections

import numpy as np
import xarray as xr

from clisops.core.average import average_over_dims as average
from clisops.ops import subset
from clisops.parameter import dimension_parameter
from clisops.parameter import time_components_parameter
from clisops.parameter import time_parameter
from clisops.project_utils import derive_ds_id

from rook.fixes import (
    WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
    FixContext,
    get_dataset_fix_provider,
)

from . import normalise
from .base import Operation, resolve_collection

coord_by_standard_name = {
    "realization": "realization",
}


def drop_time_bnds(ds: xr.Dataset) -> xr.Dataset:
    if "time_bnds" in ds.variables:
        ds = ds.drop_vars("time_bnds")
    return ds


def dataset_paths_by_id(sources):
    """Return concat input paths keyed by dataset id."""
    collection = collections.OrderedDict()

    for source in sources:
        ds_id = source.dataset_id or derive_ds_id(source.paths[0])
        collection[ds_id] = source.paths

    return collection


def apply_concat_calendar_fix(ds, fix_provider=None):
    """Apply concat-specific preparation before grouped files are combined."""
    if fix_provider is None:
        fix_provider = get_dataset_fix_provider()
    context = FixContext(
        operation="concat",
        phase="prepare",
        recipe_id=WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
    )
    return fix_provider.prepare(ds, context=context)


def apply_concat_dataset_fixes(collection, output_dir, fix_provider=None):
    """Apply concat-specific decadal fixes to each opened dataset."""
    if fix_provider is None:
        fix_provider = get_dataset_fix_provider()
    datasets = []

    for ds_id, ds in collection.items():
        context = FixContext(
            dataset_id=ds_id,
            operation="concat",
            phase="apply",
            output_dir=output_dir,
            recipe_id=WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
        )
        datasets.append(fix_provider.apply(ds, context=context))

    return datasets


def concat_dimension(dims):
    """Return the dimension name and standard name used for concat."""
    standard_name = dims[0]
    return coord_by_standard_name.get(standard_name, None), standard_name


def combine_concat_datasets(datasets, dim, standard_name):
    """Concatenate datasets and restore concat coordinate metadata."""
    ds = xr.concat(datasets, dim)
    ds = ds.assign_coords({dim: (dim, np.array(ds[dim].values, dtype="int32"))})
    ds.coords[dim].attrs = {"standard_name": standard_name}
    return drop_time_bnds(ds)


def finalise_concat_output(ds, params, dim):
    """Apply optional average and time selection to concat output."""
    if params.get("apply_average", False):
        ds = average(ds, dims=[dim])

    return subset(
        ds,
        time=params.get("time", None),
        time_components=params.get("time_components", None),
        output_type="nc",
    )


class Concat(Operation):
    def _resolve_params(self, collection, **params):
        time = time_parameter.TimeParameter(params.get("time"))
        time_components = time_components_parameter.TimeComponentsParameter(
            params.get("time_components")
        )
        dims = dimension_parameter.DimensionParameter(params.get("dims"))
        collection = resolve_collection(collection)

        self.collection = collection
        self.params = {
            "time": time,
            "time_components": time_components,
            "dims": dims,
            "apply_average": params.get("apply_average", False),
            "fix_provider": params.get("fix_provider"),
            "ignore_undetected_dims": params.get("ignore_undetected_dims"),
        }

    def calculate(self):
        self._add_output_config()
        fix_provider = get_dataset_fix_provider(self.params.get("fix_provider"))
        collection = dataset_paths_by_id(self.collection)
        norm_collection = normalise.normalise_file_groups(
            collection,
            prepare_dataset=lambda ds: apply_concat_calendar_fix(ds, fix_provider),
        )

        rs = normalise.ResultSet(vars())

        datasets = apply_concat_dataset_fixes(
            norm_collection,
            output_dir=self.params.get("output_dir", "."),
            fix_provider=fix_provider,
        )
        dims = self.params["dims"].value
        dim, standard_name = concat_dimension(dims)
        processed_ds = combine_concat_datasets(datasets, dim, standard_name)
        outputs = finalise_concat_output(processed_ds, self.params, dim)
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
    fix_provider=None,
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
        fix_provider=fix_provider,
    ).calculate()
