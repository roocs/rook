"""Operation plumbing package used by rook compatibility layers."""

from .base import Operation
from .base_selector import get_operation_base
from .average import Average, average_over_dims, average_shape, average_time
from .concat import Concat, concat
from .regrid import Regrid, regrid
from .subset import Subset, subset
from .normalise import ResultSet, normalise

__all__ = [
	"Operation",
	"get_operation_base",
	"Average",
	"average_over_dims",
	"average_shape",
	"average_time",
	"Concat",
	"concat",
	"Regrid",
	"regrid",
	"Subset",
	"subset",
	"ResultSet",
	"normalise",
]
