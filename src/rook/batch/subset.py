"""Subset-specific processor built on the common batching framework."""

import logging

from clisops.parameter.time_parameter import TimeParameter

from rook import config
from rook.io.datasets import DatasetSource, open_dataset
from rook.operations import consolidate, normalise
from rook.operations.base import Operation

from .base import BatchProcessor
from .outputs import merge_batch_outputs
from .planner import (
    SubsetBatchPlanner,
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
        timesteps_per_year, calendar, time = _source_time_metadata(source)
        if timesteps_per_year is None or calendar is None:
            logger.info(
                f"Subset batching unavailable for {source.key}: "
                "could not estimate timesteps per year or determine the calendar"
            )
            return source, []

        planner = self.get_planner()
        batching = {
            "target_timesteps": planner.target_timesteps,
            "min_batch_years": planner.min_batch_years,
            "max_batch_years": planner.max_batch_years,
        }
        batches = planner.plan(time, bounds)
        batch_years = calculate_batch_years(timesteps_per_year, **batching)
        logger.info(
            f"Subset batching plan for {source.key}: calendar={calendar}, "
            f"timesteps_per_year={timesteps_per_year}, "
            f"target_timesteps={batching['target_timesteps']}, "
            f"batch_size={batch_years} years, batches={len(batches)}"
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
    """Estimate annual timesteps and read calendar from one source file."""
    metadata_source = DatasetSource(source.dataset_id, source.paths[0])
    dataset = open_dataset(metadata_source)
    try:
        if not hasattr(dataset, "time") or dataset.time.size == 0:
            return None, None, None
        calendar = dataset.time.dt.calendar
        return (
            estimate_timesteps_per_year(dataset.time, calendar),
            calendar,
            dataset.time.load() if hasattr(dataset.time, "load") else dataset.time,
        )
    finally:
        dataset.close()


def _source_for_time(source, time):
    """Return a source containing only files that overlap one time batch."""
    if len(source.paths) == 1:
        return source
    paths = consolidate.get_files_matching_time_range(time, list(source.paths))
    return DatasetSource(source.dataset_id, paths)
