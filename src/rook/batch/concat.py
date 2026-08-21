"""Generic callback-based concat batching processor."""

import gc

import xarray as xr

from rook.diagnostics import (
    free_memory_diagnostic_enabled,
    malloc_trim,
    memory_checkpoint,
)

from .base import BatchProcessor
from .planner import calculate_batch_years, estimate_timesteps_per_year


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
        bytes_per_timestep=None,
        select_dataset=None,
        include_batch=None,
    ):
        """Execute batches sequentially with batch-local source datasets."""
        planner = self.get_planner()
        batches = planner.plan(
            planning_time,
            requested_time,
            bytes_per_timestep=bytes_per_timestep,
        )
        if include_batch is not None:
            batches = [batch for batch in batches if include_batch(batch)]

        effective_target_timesteps = planner.effective_target_timesteps(
            bytes_per_timestep
        )
        if planning_time is not None and getattr(planning_time, "size", 0) > 0:
            timesteps_per_year = estimate_timesteps_per_year(
                planning_time, planning_time.dt.calendar
            )
            batch_years = calculate_batch_years(
                timesteps_per_year,
                target_timesteps=effective_target_timesteps,
                min_batch_years=planner.min_batch_years,
                max_batch_years=planner.max_batch_years,
            )
            planned_batch_timesteps = min(
                batch_years * timesteps_per_year,
                effective_target_timesteps,
            )
        else:
            batch_years = None
            planned_batch_timesteps = None
        estimated_batch_memory_bytes = planner.estimated_process_bytes(
            planned_batch_timesteps,
            bytes_per_timestep,
        )
        memory_checkpoint(
            "concat batching plan",
            f"combined_bytes_per_timestep={bytes_per_timestep} "
            f"configured_target_timesteps={planner.target_timesteps} "
            f"memory_limit_bytes={planner.memory_limit_bytes} "
            f"memory_target_timesteps={planner.memory_target_timesteps(bytes_per_timestep)} "
            f"effective_target_timesteps={effective_target_timesteps} "
            f"planned_batch_timesteps={planned_batch_timesteps} "
            f"estimated_batch_memory_bytes={estimated_batch_memory_bytes} "
            f"annual_batch_size={batch_years} years batches={len(batches)}",
        )
        if (
            estimated_batch_memory_bytes is not None
            and planner.memory_limit_bytes is not None
            and estimated_batch_memory_bytes > planner.memory_limit_bytes
        ):
            memory_checkpoint(
                "WARNING concat one-timestep batch exceeds memory aim",
                f"estimated_batch_memory_bytes={estimated_batch_memory_bytes} "
                f"memory_limit_bytes={planner.memory_limit_bytes}",
            )

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
                memory_checkpoint(
                    "after batch selection",
                    f"{batch_label} realizations={len(selected)}",
                )

                combined = xr.concat(selected, dim=dim)
                memory_checkpoint("after realization concat", batch_label)

                outputs = operation(combined, batch.interval, index, total)
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
