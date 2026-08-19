"""Subset-specific time-batch planning."""

from .base import BaseBatchPlanner


class SubsetBatchPlanner(BaseBatchPlanner):
    """Plan batches for a subset request with closed requested bounds."""

    def plan(self, time, bounds):
        if bounds.start is None or bounds.end is None:
            return []
        return self._plan(time, bounds)
