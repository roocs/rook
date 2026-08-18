"""Calendar-aware time batching utilities for Rook operations."""

from datetime import timedelta

import cftime

from clisops.parameter.time_parameter import TimeParameter

from rook import config

from .base import Operation


class TimeBatchingOperation(Operation):
    """Operation layer that batches long daily/sub-daily time intervals."""

    def get_time_batch_size(self):
        """Return the operation-specific batch size in years."""
        raise NotImplementedError

    def get_batch_frequencies(self):
        """Return normalized frequency values eligible for batching."""
        raise NotImplementedError

    def _process_collection(self, dataset_id, collection):
        time = self.params.get("time")
        if (
            time is None
            or time.type != "interval"
            or not _has_batch_frequency(collection, self.get_batch_frequencies())
        ):
            return super()._process_collection(dataset_id, collection)

        start, end = time.get_bounds()
        if not start or not end or not hasattr(collection, "time"):
            return super()._process_collection(dataset_id, collection)

        batches = time_batches(
            start,
            end,
            collection.time.dt.calendar,
            self.get_time_batch_size(),
        )
        if len(batches) <= 1:
            return super()._process_collection(dataset_id, collection)

        outputs = []
        try:
            for start, end in batches:
                self.params["time"] = TimeParameter(f"{start}/{end}")
                outputs.extend(super()._process_collection(dataset_id, collection))
        finally:
            self.params["time"] = time
        return outputs


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


def _has_batch_frequency(dataset, batch_frequencies):
    """Return whether the dataset's frequency facet is configured for batching."""
    frequency = getattr(dataset, "attrs", {}).get("frequency")
    return (
        isinstance(frequency, str) and frequency.strip().casefold() in batch_frequencies
    )


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
