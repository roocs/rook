"""Generic callback-based concat batching processor."""

import xarray as xr

from rook.diagnostics import dataset_signature, memory_checkpoint

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
            batch_label = f"batch={index}/{total} interval={batch.interval}"
            memory_checkpoint("before batch selection", batch_label)
            selected = _select_time_batch(datasets, batch)
            if select_dataset is not None:
                selected = [select_dataset(dataset) for dataset in selected]
            memory_checkpoint(
                "after batch selection / time-component selector", batch_label
            )
            for realization, dataset in enumerate(selected, start=1):
                dataset_signature(
                    "after batch/time-component selection",
                    dataset,
                    identity=f"{batch_label} realization={realization}",
                )

            memory_checkpoint("before realization xr.concat", batch_label)
            combined = xr.concat(selected, dim=dim)
            memory_checkpoint("after realization xr.concat", batch_label)
            dataset_signature(
                "after realization concat",
                combined,
                identity=batch_label,
            )
            try:
                memory_checkpoint("before final operation/write", batch_label)
                outputs = operation(combined, batch.interval, index, total)
                memory_checkpoint("after final operation/write", batch_label)
                return outputs
            finally:
                combined.close()

        return self.execute(batches, process_time_batch)


def _select_time_batch(datasets, batch):
    if batch.start is None or batch.end is None:
        return datasets
    time_slice = slice(batch.start, batch.end)
    return [dataset.sel(time=time_slice) for dataset in datasets]
