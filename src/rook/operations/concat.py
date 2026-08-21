import collections
from collections.abc import Mapping
from functools import partial

import numpy as np
import xarray as xr

from clisops.core.average import average_over_dims as average
from clisops.core.subset import (
    assign_bounds,
    get_lat,
    get_lon,
    subset_bbox,
    subset_time,
    subset_time_by_components,
)
from clisops.ops import subset
from clisops.parameter import area_parameter
from clisops.parameter import dimension_parameter
from clisops.parameter import time_components_parameter
from clisops.parameter import time_parameter
from clisops.project_utils import derive_ds_id
from clisops.utils.dataset_utils import cf_convert_between_lon_frames

from rook import config
from rook.batch import ConcatBatch, ConcatBatchPlanner, estimate_bytes_per_timestep
from rook.batch.outputs import merge_batch_outputs
from rook.diagnostics import memory_checkpoint
from rook.fixes import (
    WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
    FixContext,
    get_dataset_fix_provider,
)

from . import consolidate, normalise
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


def apply_concat_calendar_fix(ds, provider, dataset_id=None):
    """Apply concat-specific preparation before grouped files are combined."""
    context = FixContext(
        dataset_id=dataset_id,
        operation="concat",
        phase="prepare",
        recipe_id=WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
    )
    return provider.prepare(ds, context=context)


def apply_concat_dataset_fix(dataset_id, dataset, output_dir, provider):
    """Apply the dataset-id-aware concat fix to one realization."""
    context = FixContext(
        dataset_id=dataset_id,
        operation="concat",
        phase="apply",
        output_dir=output_dir,
        recipe_id=WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
    )
    fixed = provider.apply(dataset, context=context)
    return fixed


def concat_planning_time(collection, prepare_dataset, opener=None):
    """Load one realization's time coordinates without retaining source datasets."""
    if not collection:
        return None
    if opener is None:
        opener = normalise.open_lazy_xr_dataset

    paths = next(iter(collection.values()))
    coordinates = []
    for path in paths:
        opened = opener(path)
        prepared = opened
        try:
            prepared = prepare_dataset(opened)
            if "time" in prepared.coords and prepared.time.size:
                coordinates.append(prepared.time.load().copy(deep=True))
        finally:
            prepared.close()
            if prepared is not opened:
                opened.close()

    if not coordinates:
        return None
    if len(coordinates) == 1:
        return coordinates[0]
    return xr.concat(coordinates, dim="time")


def concat_realization_bytes_per_timestep(collection, prepare_dataset, opener=None):
    """Estimate one realization's decoded temporal payload from one source file."""
    if not collection:
        return None
    if opener is None:
        opener = normalise.open_lazy_xr_dataset

    paths = next(iter(collection.values()))
    path = next(iter(paths), None)
    if path is None:
        return None
    opened = opener(path)
    prepared = opened
    try:
        prepared = prepare_dataset(opened)
        return estimate_bytes_per_timestep(prepared)
    finally:
        prepared.close()
        if prepared is not opened:
            opened.close()


def combined_concat_bytes_per_timestep(bytes_per_realization, realization_count):
    """Scale one realization's temporal payload across the concat collection."""
    if bytes_per_realization is None:
        return None
    return bytes_per_realization * realization_count


def concat_batch_paths(paths, batch):
    """Return source paths whose time ranges overlap one batch."""
    paths = tuple(paths)
    if batch.interval is None or len(paths) == 1:
        return paths
    interval = time_parameter.TimeParameter(batch.interval)
    return tuple(consolidate.get_files_matching_time_range(interval, list(paths)))


def open_concat_batch_dataset(
    dataset_id,
    paths,
    batch,
    *,
    provider,
    output_dir,
):
    """Open, normalize, and fix one realization for one time batch."""
    batch_paths = concat_batch_paths(paths, batch)
    memory_checkpoint(
        "concat batch realization paths",
        f"dataset={dataset_id} interval={batch.interval} paths={len(batch_paths)}",
    )
    if not batch_paths:
        raise ValueError(
            f"No source paths overlap concat batch {batch.interval} for {dataset_id}."
        )

    normalized = normalise.normalise_file_groups(
        collections.OrderedDict(((dataset_id, batch_paths),)),
        prepare_dataset=lambda ds: apply_concat_calendar_fix(
            ds, provider, dataset_id=dataset_id
        ),
    )[dataset_id]
    try:
        fixed = apply_concat_dataset_fix(dataset_id, normalized, output_dir, provider)
    except Exception:
        normalized.close()
        raise
    if fixed is not normalized:
        fixed.set_close(normalized.close)
    return fixed


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
    writer_label = f"batch={_index}/{_total} interval={time}"
    memory_checkpoint("before clisops writer", writer_label)
    outputs = finalise_concat_output(ds, batch_params, dim)
    memory_checkpoint("after clisops writer", writer_label)
    return outputs


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


def parsed_area(area):
    """Return low-level clisops longitude and latitude bounds."""
    if area is None:
        return None
    if isinstance(area, area_parameter.AreaParameter):
        return area.asdict()
    return area_parameter.AreaParameter(area).asdict()


def concat_dataset_selector(time_components, requested_time=None, area=None):
    """Return a lazy per-realization selector for pushed-down subset hints."""
    components = parsed_time_components(time_components)
    bounds = _requested_interval_bounds(requested_time)
    area_bounds = parsed_area(area)
    if not components and bounds is None and area_bounds is None:
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
        if area_bounds is not None:
            selected = clisops_subset_area(selected, area_bounds)
        return selected

    return select_dataset


def clisops_subset_area(dataset, area_bounds):
    """Apply the longitude-frame and bbox path used by clisops Subset."""
    longitude = get_lon(dataset)
    latitude = get_lat(dataset)
    lon_bounds = assign_bounds(area_bounds["lon_bnds"], dataset[longitude.name])
    lat_bounds = assign_bounds(area_bounds["lat_bnds"], dataset[latitude.name])
    converted, lower, upper = cf_convert_between_lon_frames(dataset, lon_bounds)
    return subset_bbox(
        converted,
        lon_bnds=(lower, upper),
        lat_bnds=lat_bounds,
    )


def effective_concat_time(requested_time, time_components):
    """Narrow planning bounds using explicit year components when available."""
    components = parsed_time_components(time_components)
    years = sorted(set((components or {}).get("year", ())))
    requested_bounds = _requested_interval_bounds(requested_time)
    if not years:
        memory_checkpoint(
            "effective concat time",
            f"requested={requested_bounds} component_years=[] effective={requested_bounds}",
        )
        return requested_time

    component_bounds = (
        f"{years[0]:04d}-01-01T00:00:00",
        f"{years[-1]:04d}-12-31T23:59:59",
    )
    if requested_bounds is None:
        bounds = component_bounds
    else:
        bounds = (
            max(requested_bounds[0], component_bounds[0]),
            min(requested_bounds[1], component_bounds[1]),
        )
    if bounds[0] > bounds[1]:
        memory_checkpoint(
            "effective concat time",
            f"requested={requested_bounds} component_years={years} effective=empty",
        )
        return requested_time
    effective = time_parameter.TimeParameter(f"{bounds[0]}/{bounds[1]}")
    memory_checkpoint(
        "effective concat time",
        f"requested={requested_bounds} component_years={years} effective={effective.get_bounds()}",
    )
    return effective


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
        area = area_parameter.AreaParameter(params.get("area"))
        dims = dimension_parameter.DimensionParameter(params.get("dims"))
        collection = resolve_collection(collection)

        self.collection = collection
        self.params = {
            "time": time,
            "time_components": time_components,
            "area": area,
            "dims": dims,
            "apply_average": params.get("apply_average", False),
            "ignore_undetected_dims": params.get("ignore_undetected_dims"),
        }

    def calculate(self):
        memory_checkpoint("concat start")
        self._add_output_config()
        provider = get_dataset_fix_provider()
        collection = dataset_paths_by_id(self.collection)
        rs = normalise.ResultSet(vars())
        dims = self.params["dims"].value
        dim, standard_name = concat_dimension(dims)
        batcher = ConcatBatch(ConcatBatchPlanner(**config.get_concat_batching_config()))
        time_components = self.params.get("time_components")
        requested_time = self.params.get("time")
        area = self.params.get("area")
        effective_time = effective_concat_time(requested_time, time_components)
        planning_dataset_id = next(iter(collection), None)
        planning_time = concat_planning_time(
            collection,
            prepare_dataset=lambda ds: apply_concat_calendar_fix(
                ds, provider, dataset_id=planning_dataset_id
            ),
        )
        realization_bytes_per_timestep = concat_realization_bytes_per_timestep(
            collection,
            prepare_dataset=lambda ds: apply_concat_calendar_fix(
                ds, provider, dataset_id=planning_dataset_id
            ),
        )
        combined_bytes_per_timestep = combined_concat_bytes_per_timestep(
            realization_bytes_per_timestep,
            len(collection),
        )
        memory_checkpoint(
            "concat planning payload",
            f"realizations={len(collection)} "
            f"realization_bytes_per_timestep={realization_bytes_per_timestep} "
            f"combined_bytes_per_timestep={combined_bytes_per_timestep}",
        )
        memory_checkpoint("before ConcatBatch")
        outputs = batcher.process(
            collection,
            planning_time=planning_time,
            dim=dim,
            open_dataset=partial(
                open_concat_batch_dataset,
                provider=provider,
                output_dir=self.params.get("output_dir", "."),
            ),
            operation=partial(
                finalise_concat_batch,
                params=self.params,
                dim=dim,
                standard_name=standard_name,
            ),
            requested_time=effective_time,
            bytes_per_timestep=combined_bytes_per_timestep,
            select_dataset=concat_dataset_selector(
                time_components,
                requested_time=requested_time,
                area=area,
            ),
            include_batch=concat_batch_filter(time_components),
        )
        output_config = config.get_concat_batch_output_config()
        outputs = merge_batch_outputs(
            outputs,
            file_namer=self._file_namer,
            output_type=self._output_type,
            **output_config,
        )
        rs.add("output", outputs)

        return rs


def concat(
    collection,
    time=None,
    time_components=None,
    area=None,
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
        area=area,
        dims=dims,
        ignore_undetected_dims=ignore_undetected_dims,
        output_dir=output_dir,
        output_type=output_type,
        split_method=split_method,
        file_namer=file_namer,
        apply_average=apply_average,
    ).calculate()
