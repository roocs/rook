"""Generic callback-based concat batching processor."""

import gc
import weakref

import xarray as xr

from rook.diagnostics import (
    dataset_signature,
    free_memory_diagnostic_enabled,
    malloc_trim,
    memory_checkpoint,
)

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
        include_batch=None,
        signature_dataset=dataset_signature,
    ):
        """Slice, combine, operate on, and close every batch sequentially."""
        batches = self.get_planner().plan(datasets, requested_time)
        if include_batch is not None:
            batches = [batch for batch in batches if include_batch(batch)]

        def process_time_batch(batch, index, total):
            batch_label = f"batch={index}/{total} interval={batch.interval}"
            selected = None
            combined = None
            batch_outputs = None
            selected_references = []
            array_references = []
            combined_reference = None
            memory_checkpoint("before batch selection", batch_label)
            selected = _select_time_batch(datasets, batch)
            if select_dataset is not None:
                selected = [select_dataset(dataset) for dataset in selected]
            selected_references = [_weak_reference(dataset) for dataset in selected]
            array_references.extend(_array_references(selected))
            memory_checkpoint(
                "after batch selection / time-component selector", batch_label
            )
            for realization, dataset in enumerate(selected, start=1):
                signature_dataset(
                    "after batch/time-component selection",
                    dataset,
                    identity=f"{batch_label} realization={realization}",
                )
            dataset = None

            memory_checkpoint("before realization xr.concat", batch_label)
            combined = xr.concat(selected, dim=dim)
            combined_reference = _weak_reference(combined)
            array_references.extend(_array_references((combined,)))
            memory_checkpoint("after realization xr.concat", batch_label)
            signature_dataset(
                "after realization concat",
                combined,
                identity=batch_label,
            )
            try:
                memory_checkpoint("before final operation/write", batch_label)
                batch_outputs = operation(combined, batch.interval, index, total)
                memory_checkpoint("after operation() returns", batch_label)
                memory_checkpoint("after final operation/write", batch_label)
            finally:
                if combined is not None:
                    combined.close()
                memory_checkpoint("after combined.close()", batch_label)
                combined = None
                memory_checkpoint("after dropping combined", batch_label)
                selected = None
                memory_checkpoint("after dropping selected", batch_label)
                free_memory = free_memory_diagnostic_enabled()
                collected = gc.collect() if free_memory else None
                retained_selected = _retained_count(selected_references)
                retained_combined = int(
                    combined_reference is not None and combined_reference() is not None
                )
                retained_arrays = _retained_count(array_references)
                memory_checkpoint(
                    "after gc.collect()" if free_memory else "gc.collect() skipped",
                    f"{batch_label} free_memory={free_memory} collected={collected} "
                    f"retained_selected={retained_selected} "
                    f"retained_combined={retained_combined} "
                    f"retained_arrays={retained_arrays}",
                )
                if free_memory:
                    trimmed = malloc_trim()
                    memory_checkpoint(
                        "after malloc_trim(0)",
                        f"{batch_label} available={trimmed is not None} released={trimmed}",
                    )

            return batch_outputs

        return self.execute(batches, process_time_batch)


def _select_time_batch(datasets, batch):
    if batch.start is None or batch.end is None:
        return datasets
    time_slice = slice(batch.start, batch.end)
    return [dataset.sel(time=time_slice) for dataset in datasets]


def _weak_reference(value):
    try:
        return weakref.ref(value)
    except TypeError:
        return None


def _array_references(datasets):
    references = []
    for dataset in datasets:
        for variable in getattr(dataset, "data_vars", {}).values():
            reference = _weak_reference(variable.variable._data)
            if reference is not None:
                references.append(reference)
    return references


def _retained_count(references):
    return sum(
        reference() is not None for reference in references if reference is not None
    )
