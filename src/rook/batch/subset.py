"""Subset-specific processor built on the common batching framework."""

import logging
from collections.abc import Mapping
from math import ceil

from clisops.parameter import time_components_parameter
from clisops.parameter.time_parameter import TimeParameter

from rook import config
from rook.io.datasets import DatasetSource, open_dataset
from rook.operations import consolidate, normalise
from rook.operations.base import Operation

from .base import BatchProcessor
from .outputs import merge_batch_outputs
from .planner import (
    SubsetBatchPlanner,
    TimeBatch,
    TimeBounds,
    calculate_batch_years,
    estimate_timesteps_per_year,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    # TODO: Replace this local sink with centralized Rook/PyWPS logging setup.
    logger.addHandler(logging.StreamHandler())


class SubsetBatch(BatchProcessor, Operation):
    """Operation layer that runs eligible subset requests in time batches."""

    def get_batching_config(self):
        """Return the established subset timestep batching configuration."""
        return config.get_batching_config()

    def get_planner(self):
        """Build the planner from the established subset batching settings."""
        if not hasattr(self, "_batch_planner"):
            self._batch_planner = SubsetBatchPlanner(**self.get_batching_config())
        return self._batch_planner

    def calculate(self):
        """Process eligible sources one time batch at a time."""
        time = self.params.get("time")
        if time is None or time.type != "interval":
            logger.info(
                "Subset batching not planned: request has no time interval; "
                "using the normal subset path"
            )
            return super().calculate()

        start, end = time.get_bounds()
        if not start or not end:
            logger.info(
                "Subset batching not planned: request has an open time boundary; "
                "using the normal subset path"
            )
            return super().calculate()

        logger.info(
            f"Planning subset batching for {len(self.collection)} source(s): "
            f"requested_time={start}/{end}"
        )
        bounds = TimeBounds(start, end)
        plans = [self._batch_plan(source, bounds) for source in self.collection]
        if not any(len(batches) > 1 for _, batches in plans):
            logger.info(
                "Subset batching not required by any source; using the normal subset path"
            )
            return super().calculate()

        self._add_output_config()
        result_set = normalise.ResultSet(vars())

        for source, batches in plans:
            outputs = self._process_source(source, batches, time)
            result_set.add(source.key, outputs)
        return result_set

    def _batch_plan(self, source, bounds):
        timesteps_per_year, calendar, time, bytes_per_timestep = _source_time_metadata(
            source
        )
        if timesteps_per_year is None or calendar is None:
            logger.info(
                f"Subset batching unavailable for {source.key}: "
                "could not estimate timesteps per year or determine the calendar"
            )
            return source, []

        planner = self.get_planner()
        effective_target_timesteps = planner.effective_target_timesteps(
            bytes_per_timestep
        )
        memory_target_timesteps = planner.memory_target_timesteps(bytes_per_timestep)
        batching = {
            "target_timesteps": effective_target_timesteps,
            "min_batch_years": planner.min_batch_years,
            "max_batch_years": planner.max_batch_years,
        }
        estimated_timesteps = _estimated_component_timesteps(
            self.params.get("time_components"), bounds, timesteps_per_year
        )
        if (
            estimated_timesteps is not None
            and estimated_timesteps <= effective_target_timesteps
        ):
            batches = [TimeBatch(bounds.start, bounds.end)]
        else:
            batches = planner.plan(
                time,
                bounds,
                bytes_per_timestep=bytes_per_timestep,
            )
            planned_batch_count = len(batches)
            batches = _batches_matching_component_years(
                batches, self.params.get("time_components")
            )
            if len(batches) != planned_batch_count:
                logger.info(
                    f"Subset batching omitted {planned_batch_count - len(batches)} "
                    f"batch(es) without selected component years for {source.key}"
                )
        batch_years = calculate_batch_years(timesteps_per_year, **batching)
        estimated_batch_memory_bytes = planner.estimated_process_bytes(
            batch_years * timesteps_per_year,
            bytes_per_timestep,
        )
        logger.info(
            f"Subset batching plan for {source.key}: calendar={calendar}, "
            f"timesteps_per_year={timesteps_per_year}, "
            f"estimated_selected_timesteps={estimated_timesteps}, "
            f"configured_target_timesteps={planner.target_timesteps}, "
            f"memory_limit_bytes={planner.memory_limit_bytes}, "
            f"bytes_per_timestep={bytes_per_timestep}, "
            f"memory_target_timesteps={memory_target_timesteps}, "
            f"effective_target_timesteps={effective_target_timesteps}, "
            f"estimated_batch_memory_bytes={estimated_batch_memory_bytes}, "
            f"batch_size={batch_years} years, batches={len(batches)}"
        )
        if (
            estimated_batch_memory_bytes is not None
            and planner.memory_limit_bytes is not None
            and estimated_batch_memory_bytes > planner.memory_limit_bytes
        ):
            logger.warning(
                f"Subset minimum batch size exceeds the memory aim for {source.key}: "
                f"estimated_batch_memory_bytes={estimated_batch_memory_bytes}, "
                f"memory_limit_bytes={planner.memory_limit_bytes}"
            )
        return source, batches

    def _process_source(self, source, batches, original_time):
        if len(batches) <= 1:
            return self._open_and_process(source)

        def process_batch(batch, index, total):
            batch_time = TimeParameter(batch.interval)
            batch_source = _source_for_time(source, batch_time)
            logger.info(
                f"Running subset batch {index}/{total} for {source.key}: "
                f"{batch.start}/{batch.end} using "
                f"{len(batch_source.paths)} source file(s)"
            )
            self.params["time"] = batch_time
            return self._open_and_process(batch_source)

        try:
            outputs = self.execute(batches, process_batch)
        finally:
            self.params["time"] = original_time

        output_config = config.get_subset_batch_output_config()
        if output_config["merge_outputs"]:
            logger.info(
                f"Merging {len(outputs)} subset batch output(s) with "
                f"max_output_bytes={output_config['max_output_bytes']} and "
                f"merge_target_bytes={output_config['merge_target_bytes']}"
            )
        merged_outputs = merge_batch_outputs(
            outputs,
            file_namer=self._file_namer,
            output_type=self._output_type,
            **output_config,
        )
        logger.info(
            f"Subset batch output post-processing complete: "
            f"inputs={len(outputs)}, outputs={len(merged_outputs)}"
        )
        return merged_outputs

    def _open_and_process(self, source):
        dataset = open_dataset(source)
        try:
            return super()._process_collection(source.key, dataset)
        finally:
            dataset.close()


def _source_time_metadata(source):
    """Estimate time cadence and decoded temporal payload from one source file."""
    metadata_source = DatasetSource(source.dataset_id, source.paths[0])
    dataset = open_dataset(metadata_source)
    try:
        if not hasattr(dataset, "time") or dataset.time.size == 0:
            return None, None, None, None
        calendar = dataset.time.dt.calendar
        return (
            estimate_timesteps_per_year(dataset.time, calendar),
            calendar,
            dataset.time.load() if hasattr(dataset.time, "load") else dataset.time,
            _estimate_bytes_per_timestep(dataset),
        )
    finally:
        dataset.close()


def _estimate_bytes_per_timestep(dataset):
    """Estimate decoded bytes contributed by variables containing time."""
    time_size = dataset.sizes.get("time") if hasattr(dataset, "sizes") else None
    variables = dataset.variables.values() if hasattr(dataset, "variables") else ()
    if not time_size:
        return None

    temporal_bytes = sum(
        variable.nbytes for variable in variables if "time" in variable.dims
    )
    return max(1, ceil(temporal_bytes / time_size)) if temporal_bytes else None


def _source_for_time(source, time):
    """Return a source containing only files that overlap one time batch."""
    if len(source.paths) == 1:
        return source
    paths = consolidate.get_files_matching_time_range(time, list(source.paths))
    return DatasetSource(source.dataset_id, paths)


def _batches_matching_component_years(batches, time_components):
    """Omit batches that cannot contain an explicitly selected year."""
    components = _parsed_time_components(time_components)
    years = set((components or {}).get("year", ()))
    if not years:
        return batches
    return [
        batch
        for batch in batches
        if batch.start is None
        or batch.end is None
        or years.intersection(range(int(batch.start[:4]), int(batch.end[:4]) + 1))
    ]


def _selected_component_years(time_components, bounds):
    """Return explicit component years within the requested interval, if any."""
    components = _parsed_time_components(time_components)
    years = (components or {}).get("year")
    if not years:
        return None
    start_year = int(bounds.start[:4])
    end_year = int(bounds.end[:4])
    return {year for year in years if start_year <= year <= end_year}


def _estimated_component_timesteps(time_components, bounds, timesteps_per_year):
    """Estimate selected timesteps using explicit year and month components."""
    components = _parsed_time_components(time_components)
    if not components:
        return None

    start_year = int(bounds.start[:4])
    end_year = int(bounds.end[:4])
    years = _selected_component_years(time_components, bounds)
    requested_year_count = end_year - start_year + 1
    year_count = len(years) if years is not None else requested_year_count
    estimate = year_count * timesteps_per_year
    reduces_selection = years is not None and year_count < requested_year_count

    months = set(components.get("month", ()))
    if 0 < len(months) < 12:
        estimate *= len(months) / 12
        reduces_selection = True
    return ceil(estimate) if reduces_selection else None


def _parsed_time_components(time_components):
    """Return time components as a plain mapping."""
    if time_components is None:
        return None
    if isinstance(time_components, time_components_parameter.TimeComponentsParameter):
        return time_components.asdict().get("time_components")
    if isinstance(time_components, Mapping):
        return time_components
    return (
        time_components_parameter.TimeComponentsParameter(time_components)
        .asdict()
        .get("time_components")
    )
