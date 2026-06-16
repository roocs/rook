"""Operation plumbing package used by rook compatibility layers."""

from .base import Operation
from .average import Average, average_over_dims, average_shape, average_time
from .concat import Concat, concat  # noqa: F401
from .regrid import Regrid, regrid  # noqa: F401
from .subset import Subset, subset  # noqa: F401
from .normalise import ResultSet, normalise  # noqa: F401

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
