"""Operation plumbing package used by rook compatibility layers."""

from .base import Operation
from .average import Average, average_over_dims, average_shape, average_time
from .normalise import ResultSet, normalise

__all__ = [
	"Operation",
	"Average",
	"average_over_dims",
	"average_shape",
	"average_time",
	"ResultSet",
	"normalise",
]
