"""Operation execution adapters and data operations."""

from .average import Average, AverageShape, AverageTime
from .base import Operation
from .execution import (
    AverageByDimension,
    AverageByShape,
    AverageByTime,
    Concat,
    Operator,
    Regrid,
    Subset,
    WORKFLOW_OPERATIONS,
    WeightedAverage,
    make_workflow_operator,
    run_average_by_dim,
    run_average_by_shape,
    run_average_by_time,
    run_concat,
    run_regrid,
    run_subset,
    run_weighted_average,
)
from .concat import Concat as ConcatOperation
from .regrid import Regrid as RegridOperation
from .subset import Subset as SubsetOperation

__all__ = [
    "WORKFLOW_OPERATIONS",
    "Average",
    "AverageByDimension",
    "AverageByShape",
    "AverageByTime",
    "AverageShape",
    "AverageTime",
    "Concat",
    "ConcatOperation",
    "Operation",
    "Operator",
    "Regrid",
    "RegridOperation",
    "Subset",
    "SubsetOperation",
    "WeightedAverage",
    "make_workflow_operator",
    "run_average_by_dim",
    "run_average_by_shape",
    "run_average_by_time",
    "run_concat",
    "run_regrid",
    "run_subset",
    "run_weighted_average",
]
