import collections
from collections.abc import Mapping
from functools import partial

import numpy as np
import xarray as xr

from clisops.core.average import average_over_dims as average
from clisops.core.subset import subset_time, subset_time_by_components
from clisops.ops import subset
from clisops.parameter import dimension_parameter
from clisops.parameter import time_components_parameter
from clisops.parameter import time_parameter
from clisops.project_utils import derive_ds_id

from rook import config
from rook.batch import ConcatBatch, ConcatBatchPlanner
from rook.diagnostics import dataset_signature, memory_checkpoint
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
DECADAL_FIX_COORDS = ("time", "reftime", "leadtime", "realization")
DECADAL_FIX_ATTRS = (
    "dataset_id",
    "project_id",
    "startdate",
    "sub_experiment_id",
    "realization_index",
)
DECADAL_DESCRIPTION_ATTRS = (
    "forcing_description",
    "physics_description",
    "initialization_description",
)


def decadal_dataset_signature(label, dataset, *, identity=None):
    """Report the coordinates and metadata produced by the decadal recipe."""
    dataset_signature(
        label,
        dataset,
        identity=identity,
        coordinate_names=DECADAL_FIX_COORDS,
        attribute_names=DECADAL_FIX_ATTRS,
        presence_attributes=DECADAL_DESCRIPTION_ATTRS,
    )


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


def apply_concat_calendar_fix(ds, provider):
    """Apply concat-specific preparation before grouped files are combined."""
    context = FixContext(
        operation="concat",
        phase="prepare",
        recipe_id=WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
    )
    return provider.prepare(ds, context=context)


def apply_concat_dataset_fixes(collection, output_dir, provider):
    """Apply concat-specific decadal fixes to each opened dataset."""
    datasets = []

    for ds_id, ds in collection.items():
        decadal_dataset_signature("before Woodpecker apply", ds, identity=ds_id)
        context = FixContext(
            dataset_id=ds_id,
            operation="concat",
            phase="apply",
            output_dir=output_dir,
            recipe_id=WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
        )
        fixed = provider.apply(ds, context=context)
        decadal_dataset_signature("after Woodpecker apply", fixed, identity=ds_id)
        datasets.append(fixed)

    return datasets


def concat_dimension(dims):
    """Return the dimension name and standard name used for concat."""
    standard_name = dims[0]
    return coord_by_standard_name.get(standard_name, None), standard_name


def prepare_concat_dataset(ds, dim, standard_name):
    """Restore concat coordinate metadata on a combined dataset."""
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
        output_dir=params.get("output_dir"),
        output_type=params.get("output_type", "netcdf"),
        split_method=params.get("split_method", "time:auto"),
        file_namer=params.get("file_namer", "standard"),
    )


def finalise_concat_batch(ds, time, _index, _total, *, params, dim, standard_name):
    """Apply concat finalization to one combined time batch."""
    ds = prepare_concat_dataset(ds, dim, standard_name)
    batch_params = dict(params)
    if time is not None:
        batch_params["time"] = time_parameter.TimeParameter(time)
    return finalise_concat_output(ds, batch_params, dim)


def parsed_time_components(time_components):
    """Return the plain component dictionary required by low-level clisops."""
    if time_components is None:
        return None
    if isinstance(time_components, time_components_parameter.TimeComponentsParameter):
        components = time_components.asdict().get("time_components")
    elif isinstance(time_components, Mapping):
        components = time_components
    else:
        components = (
            time_components_parameter.TimeComponentsParameter(time_components)
            .asdict()
            .get("time_components")
        )

    if not components:
        return None
    return {name: list(values) for name, values in dict(components).items()}


def concat_dataset_selector(time_components, requested_time=None):
    """Return a lazy per-realization selector for the effective request time."""
    components = parsed_time_components(time_components)
    bounds = _requested_interval_bounds(requested_time)
    if not components and bounds is None:
        return None

    def select_dataset(dataset):
        selected = dataset
        if bounds is not None:
            selected = subset_time(
                selected,
                start_date=bounds[0],
                end_date=bounds[1],
            )
        if components:
            try:
                selected = subset_time_by_components(
                    selected,
                    time_components=components,
                )
            except KeyError:
                selected = selected.isel(time=slice(0, 0))
        return selected

    return select_dataset


def effective_concat_time(requested_time, time_components):
    """Narrow planning bounds using explicit year components when available."""
    components = parsed_time_components(time_components)
    years = sorted(set((components or {}).get("year", ())))
    if not years:
        return requested_time

    component_bounds = (
        f"{years[0]:04d}-01-01T00:00:00",
        f"{years[-1]:04d}-12-31T23:59:59",
    )
    requested_bounds = _requested_interval_bounds(requested_time)
    if requested_bounds is None:
        bounds = component_bounds
    else:
        bounds = (
            max(requested_bounds[0], component_bounds[0]),
            min(requested_bounds[1], component_bounds[1]),
        )
    if bounds[0] > bounds[1]:
        return requested_time
    return time_parameter.TimeParameter(f"{bounds[0]}/{bounds[1]}")


def concat_batch_filter(time_components):
    """Return a generic batch predicate for explicit component years."""
    components = parsed_time_components(time_components)
    years = set((components or {}).get("year", ()))
    if not years:
        return None

    def includes_selected_year(batch):
        if batch.start is None or batch.end is None:
            return True
        return bool(
            years.intersection(range(int(batch.start[:4]), int(batch.end[:4]) + 1))
        )

    return includes_selected_year


def _requested_interval_bounds(requested_time):
    if requested_time is None or getattr(requested_time, "type", None) != "interval":
        return None
    start, end = requested_time.get_bounds()
    if not start or not end:
        return None
    return start, end


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
            "ignore_undetected_dims": params.get("ignore_undetected_dims"),
        }

    def calculate(self):
        memory_checkpoint("concat start")
        self._add_output_config()
        provider = get_dataset_fix_provider()
        collection = dataset_paths_by_id(self.collection)

        # Concat intentionally does not use the base operation flow:
        # - keep paths grouped by dataset id;
        # - prepare each opened file by fixing its calendar before time concat;
        # - apply dataset-id-aware fixes after each group has been opened.
        memory_checkpoint("before normalise_file_groups")
        norm_collection = normalise.normalise_file_groups(
            collection,
            prepare_dataset=lambda ds: apply_concat_calendar_fix(ds, provider),
        )
        memory_checkpoint("after normalise_file_groups")

        rs = normalise.ResultSet(vars())

        memory_checkpoint("before Woodpecker dataset fixes")
        datasets = apply_concat_dataset_fixes(
            norm_collection,
            output_dir=self.params.get("output_dir", "."),
            provider=provider,
        )
        memory_checkpoint("after Woodpecker dataset fixes")
        dims = self.params["dims"].value
        dim, standard_name = concat_dimension(dims)
        batcher = ConcatBatch(ConcatBatchPlanner(**config.get_batching_config()))
        time_components = self.params.get("time_components")
        requested_time = self.params.get("time")
        memory_checkpoint("before ConcatBatch")
        outputs = batcher.process(
            datasets,
            dim=dim,
            operation=partial(
                finalise_concat_batch,
                params=self.params,
                dim=dim,
                standard_name=standard_name,
            ),
            requested_time=effective_concat_time(requested_time, time_components),
            select_dataset=concat_dataset_selector(
                time_components,
                requested_time=requested_time,
            ),
            include_batch=concat_batch_filter(time_components),
            signature_dataset=decadal_dataset_signature,
        )
        memory_checkpoint("after ConcatBatch")
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
    ).calculate()
