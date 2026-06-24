"""Operation execution adapters and data operations."""

from .execution import (
    AverageByDimension,
    AverageByShape,
    AverageByTime,
    Concat,
    Operator,
    Regrid,
    Subset,
    WeightedAverage,
    run_average_by_dim,
    run_average_by_shape,
    run_average_by_time,
    run_concat,
    run_regrid,
    run_subset,
    run_weighted_average,
)

__all__ = [
    "AverageByDimension",
    "AverageByShape",
    "AverageByTime",
    "Concat",
    "Operator",
    "Regrid",
    "Subset",
    "WeightedAverage",
    "run_average_by_dim",
    "run_average_by_shape",
    "run_average_by_time",
    "run_concat",
    "run_regrid",
    "run_subset",
    "run_weighted_average",
]
