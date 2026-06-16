"""Operation plumbing package used by rook compatibility layers."""

from .base import Operation
from .average import Average, average_over_dims, average_shape, average_time
from .concat import Concat, concat
from .regrid import Regrid, regrid
from .subset import Subset, subset
from .normalise import ResultSet, normalise

__all__ = [
    "Average",
    "Concat",
    "Operation",
    "Regrid",
    "ResultSet",
    "Subset",
    "average_over_dims",
    "average_shape",
    "average_time",
]
