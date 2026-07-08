"""Request decision values."""

from collections import OrderedDict
from dataclasses import dataclass

from rook.io.datasets import DatasetSource

from .base import RequestDecision as RequestDecisionBase


@dataclass(frozen=True)
class ReturnOriginalFiles(RequestDecisionBase):
    """Decision to return catalog file URLs without running an operation."""

    project: str
    search_result: object | None = None
    original_file_urls: OrderedDict | None = None

    @property
    def returns_original_files(self):
        """Return whether this request should bypass processing."""
        return True

    @property
    def dataset_sources(self):
        """Return no prepared operation sources for original-file responses."""
        return ()


@dataclass(frozen=True)
class RunOperation(RequestDecisionBase):
    """Decision to run an operation on the requested or prepared sources."""

    project: str
    search_result: object | None = None
    dataset_sources: tuple[DatasetSource, ...] = ()

    @property
    def returns_original_files(self):
        """Return whether this request should bypass processing."""
        return False

    @property
    def original_file_urls(self):
        """Return no original file URLs for operation responses."""
        return None


@dataclass(frozen=True)
class InvalidRequest(RequestDecisionBase):
    """Decision value reserved for explicit invalid-request outcomes."""

    message: str

    @property
    def returns_original_files(self):
        """Return whether this request should bypass processing."""
        return False


RequestDecision = InvalidRequest | ReturnOriginalFiles | RunOperation
