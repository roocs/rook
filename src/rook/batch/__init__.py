"""Reusable time-batching infrastructure for Rook operations."""

from .base import BatchProcessor
from .concat import ConcatBatch
from .planner import (
    BaseBatchPlanner,
    ConcatBatchPlanner,
    SubsetBatchPlanner,
    TimeBatch,
    TimeBounds,
    calculate_batch_years,
    estimate_timesteps_per_year,
    time_batches,
)
from .subset import SubsetBatch

__all__ = [
    "BaseBatchPlanner",
    "BatchProcessor",
    "ConcatBatch",
    "ConcatBatchPlanner",
    "SubsetBatch",
    "SubsetBatchPlanner",
    "TimeBatch",
    "TimeBounds",
    "calculate_batch_years",
    "estimate_timesteps_per_year",
    "time_batches",
]
