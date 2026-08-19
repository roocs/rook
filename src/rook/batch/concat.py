"""Generic callback-based concat batching processor."""

import xarray as xr

from .base import BatchProcessor


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
        select_dataset=None,
    ):
        """Slice, combine, operate on, and close every batch sequentially."""
        batches = self.get_planner().plan(datasets, requested_time)

        def process_time_batch(batch, index, total):
            selected = _select_time_batch(datasets, batch)
            if select_dataset is not None:
                selected = [select_dataset(dataset) for dataset in selected]
            combined = xr.concat(selected, dim=dim)
            try:
                return operation(combined, batch.interval, index, total)
            finally:
                combined.close()

        return self.execute(batches, process_time_batch)


def _select_time_batch(datasets, batch):
    if batch.start is None or batch.end is None:
        return datasets
    time_slice = slice(batch.start, batch.end)
    return [dataset.sel(time=time_slice) for dataset in datasets]
