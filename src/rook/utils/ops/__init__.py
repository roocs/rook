"""Operation plumbing package used by rook compatibility layers."""

from .base import Operation
from .normalise import ResultSet, normalise

__all__ = ["Operation", "ResultSet", "normalise"]
