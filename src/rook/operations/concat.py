import collections
from collections.abc import Mapping
from functools import partial
from pathlib import Path

import dask
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
from clisops.utils.file_namers import get_file_namer
from clisops.utils.output_utils import get_format_engine

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
    write_path = config.get_concat_write_path()
    writer_label = f"batch={_index}/{_total} interval={time} writer={write_path}"

    if write_path == "xarray":
        if batch_params.get("apply_average", False):
            ds = average(ds, dims=[dim])
        memory_checkpoint("before direct xarray/netCDF writer", writer_label)
        outputs = write_concat_batch_direct(ds, batch_params, _index)
        memory_checkpoint("after direct xarray/netCDF writer", writer_label)
        return outputs

    memory_checkpoint("before clisops subset writer", writer_label)
    outputs = finalise_concat_output(ds, batch_params, dim)
    memory_checkpoint("after clisops subset writer", writer_label)
    return outputs


def write_concat_batch_direct(ds, params, batch_index):
    """Write one already-selected concat batch without clisops Subset."""
    output_type = params.get("output_type", "netcdf")
    if output_type not in {"netcdf", "nc"}:
        raise ValueError(
            "The diagnostic xarray concat writer supports NetCDF output only."
        )

    output_dir = Path(params.get("output_dir") or Path.cwd()).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    namer = get_file_namer(params.get("file_namer", "standard"))()
    output_path = output_dir / namer.get_file_name(ds, fmt=output_type)
    if output_path.exists():
        output_path = output_path.with_name(
            f"{output_path.stem}_batch-{batch_index:03d}{output_path.suffix}"
        )

    engine = get_format_engine(output_type)
    delayed_write = None
    memory_checkpoint(
        "before direct xarray to_netcdf graph",
        f"batch={batch_index} path={output_path}",
    )
    try:
        delayed_write = ds.to_netcdf(
            output_path,
            engine=engine,
            compute=False,
        )
        memory_checkpoint(
            "after direct xarray to_netcdf graph",
            f"batch={batch_index} path={output_path}",
        )
        with dask.config.set(scheduler="synchronous"):
            memory_checkpoint(
                "before direct xarray delayed write",
                f"batch={batch_index} path={output_path}",
            )
            delayed_write.compute()
            memory_checkpoint(
                "after direct xarray delayed write",
                f"batch={batch_index} path={output_path}",
            )
    finally:
        delayed_write = None

    return [output_path.as_posix()]


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
    memory_checkpoint(
        "concat selector configured",
        f"time_components={components} requested_bounds={bounds} area={area_bounds}",
    )
    if not components and bounds is None and area_bounds is None:
        return None

    def select_dataset(dataset):
        selected = dataset
        memory_checkpoint(
            "concat selector before selection",
            f"time={selected.sizes.get('time', 0)}",
        )
        if bounds is not None:
            selected = subset_time(
                selected,
                start_date=bounds[0],
                end_date=bounds[1],
            )
        memory_checkpoint(
            "concat selector after subset_time",
            f"time={selected.sizes.get('time', 0)} bounds={bounds}",
        )
        if components:
            try:
                selected = subset_time_by_components(
                    selected,
                    time_components=components,
                )
            except KeyError:
                selected = selected.isel(time=slice(0, 0))
        memory_checkpoint(
            "concat selector after subset_time_by_components",
            f"time={selected.sizes.get('time', 0)} time_components={components}",
        )
        memory_checkpoint(
            "concat selector before area selection",
            _spatial_sizes(selected),
        )
        if area_bounds is not None:
            selected = clisops_subset_area(selected, area_bounds)
        memory_checkpoint(
            "concat selector after area selection",
            _spatial_sizes(selected),
        )
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


def _spatial_sizes(dataset):
    names = ("lat", "latitude", "y", "lon", "longitude", "x")
    sizes = [f"{name}={dataset.sizes[name]}" for name in names if name in dataset.sizes]
    return " ".join(sizes) or "spatial_sizes=unavailable"


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
        batcher = ConcatBatch(ConcatBatchPlanner(**config.get_concat_batching_config()))
        time_components = self.params.get("time_components")
        requested_time = self.params.get("time")
        area = self.params.get("area")
        effective_time = effective_concat_time(requested_time, time_components)
        memory_checkpoint(
            "ConcatBatchPlanner input",
            f"requested_time={_requested_interval_bounds(effective_time)}",
        )
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
            requested_time=effective_time,
            select_dataset=concat_dataset_selector(
                time_components,
                requested_time=requested_time,
                area=area,
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
