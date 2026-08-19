"""Generic callback-based concat batching processor."""

from .base import BatchProcessor


class ConcatBatch(BatchProcessor):
    """Plan time batches and execute an operation callback for each one."""

    def __init__(self, planner):
        self.planner = planner

    def process(self, time, process_batch, *, start=None, end=None, calendar=None):
        batches = self.planner.plan(
            time,
            start=start,
            end=end,
            calendar=calendar,
        )
        return self.execute(batches, process_batch)
