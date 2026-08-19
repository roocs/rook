"""Concat-specific time-batch planning."""

from .base import BaseBatchPlanner, TimeBounds


class ConcatBatchPlanner(BaseBatchPlanner):
    """Plan concat batches from a representative time coordinate."""

    def plan(self, time, requested_time=None):
        return self._plan(
            time,
            _requested_bounds(requested_time),
        )


def _requested_bounds(time):
    if time is None or getattr(time, "type", None) != "interval":
        return None
    start, end = time.get_bounds()
    if not start or not end:
        return None
    return TimeBounds(start, end)
