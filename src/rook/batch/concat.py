"""Generic callback-based concat batching processor."""

import xarray as xr

from .base import BatchProcessor
from .planner import TimeBounds


class ConcatBatch(BatchProcessor):
    """Slice concat inputs by time and execute one callback per batch."""

    def __init__(self, planner):
        self._planner = planner

    def get_planner(self):
        return self._planner

    def process(
        self,
        datasets,
        *,
        dim,
        operation,
        requested_time=None,
    ):
        """Slice, combine, operate on, and close every batch sequentially."""
        time = _representative_time(datasets)
        bounds = _requested_bounds(requested_time)

        def process_time_batch(batch, index, total):
            selected = _select_time_batch(datasets, batch)
            combined = xr.concat(selected, dim=dim)
            try:
                return operation(combined, batch.interval, index, total)
            finally:
                combined.close()

        return super().process(
            time,
            process_time_batch,
            bounds=bounds,
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


def _select_time_batch(datasets, batch):
    if batch.start is None or batch.end is None:
        return datasets
    time_slice = slice(batch.start, batch.end)
    return [dataset.sel(time=time_slice) for dataset in datasets]
