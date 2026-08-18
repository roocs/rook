"""Calendar-aware time batching utilities for Rook operations."""

from datetime import timedelta

import cftime
from loguru import logger

from clisops.parameter.time_parameter import TimeParameter

from rook import config
from rook.io.datasets import DatasetSource, open_dataset

from . import consolidate, normalise
from .base import Operation


class TimeBatchingOperation(Operation):
    """Operation layer that batches long daily/sub-daily time intervals."""

    def get_time_batch_size(self):
        """Return the operation-specific batch size in years."""
        raise NotImplementedError

    def get_batch_frequencies(self):
        """Return normalized frequency values eligible for batching."""
        raise NotImplementedError

    def calculate(self):
        """Process eligible sources one time batch at a time."""
        time = self.params.get("time")
        if time is None or time.type != "interval":
            return super().calculate()

        start, end = time.get_bounds()
        if not start or not end:
            return super().calculate()

        plans = [self._batch_plan(source, start, end) for source in self.collection]
        if not any(len(batches) > 1 for _, batches in plans):
            return super().calculate()

        self._add_output_config()
        result_set = normalise.ResultSet(vars())

        for source, batches in plans:
            outputs = self._process_source(source, batches, time)
            result_set.add(source.key, outputs)
        return result_set

    def _batch_plan(self, source, start, end):
        frequency, calendar = _source_time_metadata(source)
        if calendar is None:
            return source, []

        batches = time_batches(start, end, calendar, self.get_time_batch_size())
        if len(batches) <= 1:
            return source, batches
        if frequency not in self.get_batch_frequencies():
            logger.info(
                f"Subset batching skipped for {source.key}: "
                f"frequency={frequency!r} is not configured"
            )
            return source, []

        logger.info(
            f"Subset batching enabled for {source.key}: frequency={frequency}, "
            f"batches={len(batches)}, batch_size={self.get_time_batch_size()} years"
        )
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
        return outputs

    def _open_and_process(self, source):
        dataset = open_dataset(source)
        try:
            return super()._process_collection(source.key, dataset)
        finally:
            dataset.close()


class SubsetTimeBatchingOperation(TimeBatchingOperation):
    """Time-batching layer configured specifically for the subset operation."""

    def get_time_batch_size(self):
        return config.get_subset_time_batch_size()

    def get_batch_frequencies(self):
        return config.get_batch_frequencies()


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
    """Read frequency and calendar without opening the complete source collection."""
    metadata_source = DatasetSource(source.dataset_id, source.paths[0])
    dataset = open_dataset(metadata_source)
    try:
        frequency = dataset.attrs.get("frequency")
        if isinstance(frequency, str):
            frequency = frequency.strip().casefold()
        else:
            frequency = None
        calendar = dataset.time.dt.calendar if hasattr(dataset, "time") else None
        return frequency, calendar
    finally:
        dataset.close()


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
    return cftime.datetime(year, month, day, hour, minute, second, calendar=calendar)


def _add_years(value, years):
    """Add calendar years, clamping leap-only dates to the month end."""
    day = value.day
    while day:
        try:
            return cftime.datetime(
                value.year + years,
                value.month,
                day,
                value.hour,
                value.minute,
                value.second,
                calendar=value.calendar,
            )
        except ValueError:
            day -= 1
    raise ValueError(f"Could not add {years} years to {value!s}.")


def _format_time(value):
    return (
        f"{value.year:04d}-{value.month:02d}-{value.day:02d}"
        f"T{value.hour:02d}:{value.minute:02d}:{value.second:02d}"
    )
