"""Shared calendar-aware adaptive batch planning mechanics."""

from collections import Counter
from dataclasses import dataclass
from datetime import timedelta
from math import ceil, floor

import cftime
import numpy as np


MEMORY_AMPLIFICATION_FACTOR = 2


@dataclass(frozen=True)
class TimeBatch:
    """One inclusive time interval in a batching plan."""

    start: str | None
    end: str | None

    @property
    def interval(self):
        """Return the interval in the form accepted by clisops."""
        if self.start is None or self.end is None:
            return None
        return f"{self.start}/{self.end}"


@dataclass(frozen=True)
class TimeBounds:
    """Optional requested bounds supplied to a time-batch plan."""

    start: str | None
    end: str | None


class BaseBatchPlanner:
    """Shared calendar-aware adaptive time-batch planning mechanics."""

    def __init__(
        self,
        *,
        target_timesteps,
        memory_limit_bytes=None,
        min_batch_years=1,
        max_batch_years=10,
    ):
        self.target_timesteps = target_timesteps
        self.memory_limit_bytes = memory_limit_bytes
        self.min_batch_years = min_batch_years
        self.max_batch_years = max_batch_years

    def memory_target_timesteps(self, bytes_per_timestep):
        """Estimate timesteps fitting the memory aim with writer headroom."""
        if self.memory_limit_bytes is None or not bytes_per_timestep:
            return None
        estimated_process_bytes_per_timestep = self.estimated_process_bytes(
            1, bytes_per_timestep
        )
        return max(
            1,
            floor(self.memory_limit_bytes / estimated_process_bytes_per_timestep),
        )

    @staticmethod
    def estimated_process_bytes(timesteps, bytes_per_timestep):
        """Estimate peak process bytes for a decoded temporal payload."""
        if not timesteps or not bytes_per_timestep:
            return None
        return timesteps * bytes_per_timestep * MEMORY_AMPLIFICATION_FACTOR

    def effective_target_timesteps(self, bytes_per_timestep=None):
        """Return the stricter configured timestep or estimated memory target."""
        memory_target = self.memory_target_timesteps(bytes_per_timestep)
        if memory_target is None:
            return self.target_timesteps
        return min(self.target_timesteps, memory_target)

    def _plan(self, time, bounds=None, *, target_timesteps=None):
        """Build batches from one representative coordinate and optional bounds."""
        start = bounds.start if bounds is not None else None
        end = bounds.end if bounds is not None else None
        if time is None or getattr(time, "size", 0) == 0:
            return [TimeBatch(start, end)]

        calendar = time.dt.calendar
        if start is None:
            start = _format_time_value(time.values[0], calendar)
        if end is None:
            end = _format_time_value(time.values[-1], calendar)

        batch_years = calculate_batch_years(
            estimate_timesteps_per_year(time, calendar),
            target_timesteps=(
                self.target_timesteps if target_timesteps is None else target_timesteps
            ),
            min_batch_years=self.min_batch_years,
            max_batch_years=self.max_batch_years,
        )
        return [
            TimeBatch(batch_start, batch_end)
            for batch_start, batch_end in time_batches(
                start, end, calendar, batch_years
            )
        ]


def calculate_batch_years(
    timesteps_per_year, target_timesteps, min_batch_years, max_batch_years
):
    """Derive a clamped batch length that does not exceed the timestep target."""
    batch_years = floor(target_timesteps / timesteps_per_year)
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


def timestep_batches(time, bounds, target_timesteps):
    """Split a coordinate into consecutive batches capped by timestep count."""
    if time is None or getattr(time, "size", 0) == 0:
        start = bounds.start if bounds is not None else None
        end = bounds.end if bounds is not None else None
        return [TimeBatch(start, end)]

    calendar = time.dt.calendar
    start = (
        bounds.start
        if bounds is not None and bounds.start is not None
        else _format_time_value(time.values[0], calendar)
    )
    end = (
        bounds.end
        if bounds is not None and bounds.end is not None
        else _format_time_value(time.values[-1], calendar)
    )
    selected = time.sel(time=slice(start, end))
    values = selected.values
    if len(values) <= target_timesteps:
        return [TimeBatch(start, end)]

    batches = []
    batch_start = start
    for index in range(target_timesteps, len(values), target_timesteps):
        next_start = _format_time_value(values[index], calendar)
        next_start_value = _parse_time(next_start, calendar)
        batches.append(
            TimeBatch(
                batch_start,
                _format_time(next_start_value - timedelta(seconds=1)),
            )
        )
        batch_start = next_start
    batches.append(TimeBatch(batch_start, end))
    return batches


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


def estimate_bytes_per_timestep(dataset):
    """Estimate decoded bytes contributed by variables containing time."""
    time_size = dataset.sizes.get("time") if hasattr(dataset, "sizes") else None
    variables = dataset.variables.values() if hasattr(dataset, "variables") else ()
    if not time_size:
        return None

    temporal_bytes = sum(
        variable.nbytes for variable in variables if "time" in variable.dims
    )
    return max(1, ceil(temporal_bytes / time_size)) if temporal_bytes else None


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


def _format_time_value(value, calendar):
    if isinstance(value, np.datetime64):
        value = value.astype("datetime64[s]").item()
    if not hasattr(value, "year"):
        value = cftime.num2date(value, "seconds since 1970-01-01", calendar=calendar)
    return _format_time(value)


def _parse_time(value, calendar):
    if "T" not in value:
        value = f"{value}T00:00:00"
    date, clock = value.split("T", 1)
    date_parts = [int(part) for part in date.split("-")]
    if len(date_parts) == 1:
        date_parts.extend((1, 1))
    elif len(date_parts) == 2:
        date_parts.append(1)
    clock_parts = [int(float(part)) for part in clock.split(":")]
    clock_parts.extend([0] * (3 - len(clock_parts)))
    year, month, day = date_parts
    hour, minute, second = clock_parts[:3]
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
