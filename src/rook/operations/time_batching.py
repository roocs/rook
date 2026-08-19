"""Compatibility imports for batching code moved to :mod:`rook.batch`."""

from rook.batch import (
    SubsetBatch,
    TimeBatchPlanner,
    calculate_batch_years,
    estimate_timesteps_per_year,
    time_batches,
)

# Keep the old internal class names available to downstream imports.
TimeBatchingOperation = SubsetBatch
SubsetTimeBatchingOperation = SubsetBatch

__all__ = [
    "SubsetTimeBatchingOperation",
    "TimeBatchingOperation",
    "TimeBatchPlanner",
    "calculate_batch_years",
    "estimate_timesteps_per_year",
    "time_batches",
]
