"""Generic callback-based concat batching processor."""

import gc

import xarray as xr

from rook.diagnostics import (
    dataset_signature,
    free_memory_diagnostic_enabled,
    malloc_trim,
    memory_checkpoint,
)

from .base import BatchProcessor


class ConcatBatch(BatchProcessor):
    """Open, combine, operate on, and close source datasets one batch at a time."""

    def __init__(self, planner):
        self._planner = planner

    def get_planner(self):
        return self._planner

    def process(
        self,
        collection,
        *,
        planning_time,
        dim,
        open_dataset,
        operation,
        requested_time=None,
        select_dataset=None,
        include_batch=None,
        signature_dataset=dataset_signature,
    ):
        """Execute batches sequentially with batch-local source datasets."""
        batches = self.get_planner().plan(planning_time, requested_time)
        if include_batch is not None:
            batches = [batch for batch in batches if include_batch(batch)]

        def process_time_batch(batch, index, total):
            batch_label = f"batch={index}/{total} interval={batch.interval}"
            datasets = []
            selected = []
            combined = None

            try:
                memory_checkpoint("before opening batch inputs", batch_label)
                for dataset_id, paths in collection.items():
                    datasets.append(open_dataset(dataset_id, paths, batch))
                memory_checkpoint(
                    "after opening batch inputs",
                    f"{batch_label} realizations={len(datasets)}",
                )

                selected = [_select_time_batch(dataset, batch) for dataset in datasets]
                if select_dataset is not None:
                    selected = [select_dataset(dataset) for dataset in selected]
                for realization, dataset in enumerate(selected, start=1):
                    signature_dataset(
                        "after batch selection",
                        dataset,
                        identity=f"{batch_label} realization={realization}",
                    )

                combined = xr.concat(selected, dim=dim)
                memory_checkpoint("after realization concat", batch_label)
                signature_dataset(
                    "after realization concat", combined, identity=batch_label
                )

                outputs = operation(combined, batch.interval, index, total)
                memory_checkpoint("after write", batch_label)
                return outputs
            finally:
                if combined is not None:
                    combined.close()
                for dataset in datasets:
                    dataset.close()
                selected.clear()
                datasets.clear()
                memory_checkpoint("after closing batch inputs", batch_label)

                if free_memory_diagnostic_enabled():
                    collected = gc.collect()
                    memory_checkpoint(
                        "after gc.collect()",
                        f"{batch_label} collected={collected}",
                    )
                    trimmed = malloc_trim()
                    memory_checkpoint(
                        "after malloc_trim(0)",
                        f"{batch_label} available={trimmed is not None} released={trimmed}",
                    )

        return self.execute(batches, process_time_batch)


def _select_time_batch(dataset, batch):
    if batch.start is None or batch.end is None:
        return dataset
    return dataset.sel(time=slice(batch.start, batch.end))
