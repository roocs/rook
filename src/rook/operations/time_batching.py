"""Calendar-aware time batching utilities for Rook operations."""

from collections import Counter
from datetime import timedelta
import logging

import cftime
import numpy as np

from clisops.parameter.time_parameter import TimeParameter

from rook import config
from rook.io.datasets import DatasetSource, open_dataset

from . import batch_outputs, consolidate, normalise
from .base import Operation

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    # TODO: Replace this local sink with centralized Rook/PyWPS logging setup.
    logger.addHandler(logging.StreamHandler())


class TimeBatchingOperation(Operation):
    """Operation layer that limits approximate time-axis size per batch."""

    def get_batching_config(self):
        """Return operation-specific timestep batching configuration."""
        raise NotImplementedError

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
        plans = [self._batch_plan(source, start, end) for source in self.collection]
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

    def _batch_plan(self, source, start, end):
        timesteps_per_year, calendar = _source_time_metadata(source)
        if timesteps_per_year is None or calendar is None:
            logger.info(
                f"Subset batching unavailable for {source.key}: "
                "could not estimate timesteps per year or determine the calendar"
            )
            return source, []

        batching = self.get_batching_config()
        batch_years = calculate_batch_years(timesteps_per_year, **batching)
        batches = time_batches(start, end, calendar, batch_years)
        logger.info(
            f"Subset batching plan for {source.key}: calendar={calendar}, "
            f"timesteps_per_year={timesteps_per_year}, "
            f"target_timesteps={batching['target_timesteps']}, "
            f"batch_size={batch_years} years, batches={len(batches)}"
        )
        if len(batches) <= 1:
            return source, batches
        return source, batches

    def _process_source(self, source, batches, original_time):
        if len(batches) <= 1:
            return self._open_and_process(source)

        outputs = []
        try:
            for index, (start, end) in enumerate(batches, start=1):
                batch_time = TimeParameter(f"{start}/{end}")
                batch_source = _source_for_time(source, batch_time)
                logger.info(
                    f"Running subset batch {index}/{len(batches)} for {source.key}: "
                    f"{start}/{end} using {len(batch_source.paths)} source file(s)"
                )
                self.params["time"] = batch_time
                outputs.extend(self._open_and_process(batch_source))
        finally:
            self.params["time"] = original_time
        output_config = config.get_subset_batch_output_config()
        if output_config["merge_outputs"]:
            logger.info(
                f"Merging {len(outputs)} subset batch output(s) with "
                f"max_output_bytes={output_config['max_output_bytes']} and "
                f"merge_target_bytes={output_config['merge_target_bytes']}"
            )
        merged_outputs = batch_outputs.merge_batch_outputs(
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


class SubsetTimeBatchingOperation(TimeBatchingOperation):
    """Time-batching layer configured specifically for the subset operation."""

    def get_batching_config(self):
        return config.get_subset_batching_config()


def calculate_batch_years(
    timesteps_per_year, target_timesteps, min_batch_years, max_batch_years
):
    """Derive a clamped batch length from an estimated annual timestep count."""
    batch_years = round(target_timesteps / timesteps_per_year)
    return max(min_batch_years, min(max_batch_years, batch_years))


def time_batches(start_value, end_value, calendar, batch_size):
    """Split inclusive time bounds into consecutive calendar-year batches."""
    start = _parse_time(start_value, calendar)
    end = _parse_time(end_value, calendar)
    batches = []
    batch_start = start

    while batch_start <= end:
        next_start = _add_years(batch_start, batch_size)
        if next_start > end:
            batches.append((_format_time(batch_start), _format_time(end)))
            break
        batches.append(
            (
                _format_time(batch_start),
                _format_time(next_start - timedelta(seconds=1)),
            )
        )
        batch_start = next_start

    return batches


def _source_time_metadata(source):
    """Estimate annual timesteps and read calendar from one source file."""
    metadata_source = DatasetSource(source.dataset_id, source.paths[0])
    dataset = open_dataset(metadata_source)
    try:
        if not hasattr(dataset, "time") or dataset.time.size == 0:
            return None, None
        calendar = dataset.time.dt.calendar
        return estimate_timesteps_per_year(dataset.time, calendar), calendar
    finally:
        dataset.close()


def estimate_timesteps_per_year(time, calendar):
    """Estimate annual timestep count from the observed time-axis cadence."""
    values = getattr(time, "values", ())
    if len(values) >= 2:
        elapsed_seconds = _timedelta_seconds(values[-1] - values[0])
        if elapsed_seconds > 0:
            observed_intervals = len(values) - 1
            seconds_per_year = _calendar_days_per_year(calendar) * 86400
            return max(
                1, round(observed_intervals * seconds_per_year / elapsed_seconds)
            )

    years = Counter(int(year) for year in time.dt.year.values)
    return max(years.values())


def _timedelta_seconds(value):
    if hasattr(value, "total_seconds"):
        return value.total_seconds()
    return float(value / np.timedelta64(1, "s"))


def _calendar_days_per_year(calendar):
    return {
        "360_day": 360,
        "365_day": 365,
        "noleap": 365,
        "366_day": 366,
        "all_leap": 366,
    }.get(calendar, 365.2425)


def _source_for_time(source, time):
    """Return a source containing only files that overlap one time batch."""
    if len(source.paths) == 1:
        return source
    paths = consolidate.get_files_matching_time_range(time, list(source.paths))
    return DatasetSource(source.dataset_id, paths)


def _parse_time(value, calendar):
    date, clock = value.split("T", 1)
    year, month, day = (int(part) for part in date.split("-"))
    hour, minute, second = (int(part) for part in clock.split(":"))
    return _calendar_datetime(year, month, day, hour, minute, second, calendar)


def _add_years(value, years):
    """Add calendar years, clamping leap-only dates to the month end."""
    return _calendar_datetime(
        value.year + years,
        value.month,
        value.day,
        value.hour,
        value.minute,
        value.second,
        value.calendar,
    )


def _calendar_datetime(year, month, day, hour, minute, second, calendar):
    """Create a calendar date, clamping invalid month-end days downward."""
    month_start = cftime.datetime(
        year, month, 1, hour, minute, second, calendar=calendar
    )
    return cftime.datetime(
        year,
        month,
        min(day, month_start.daysinmonth),
        hour,
        minute,
        second,
        calendar=calendar,
    )


def _format_time(value):
    return (
        f"{value.year:04d}-{value.month:02d}-{value.day:02d}"
        f"T{value.hour:02d}:{value.minute:02d}:{value.second:02d}"
    )
