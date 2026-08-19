"""Concat-specific time-batch planning."""

from .base import BaseBatchPlanner, TimeBounds


class ConcatBatchPlanner(BaseBatchPlanner):
    """Plan batches across the time coordinate shared by concat inputs."""

    def plan(self, datasets, requested_time=None):
        return self._plan(
            _representative_time(datasets),
            _requested_bounds(requested_time),
        )


def _representative_time(datasets):
    for dataset in datasets:
        if "time" in dataset.coords:
            return dataset.time
    return None


def _requested_bounds(time):
    if time is None or getattr(time, "type", None) != "interval":
        return None
    start, end = time.get_bounds()
    if not start or not end:
        return None
    return TimeBounds(start, end)
