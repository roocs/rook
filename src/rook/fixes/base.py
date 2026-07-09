"""Base classes for dataset fix providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import importlib.util


@dataclass(frozen=True)
class FixContext:
    """Rook-side context passed to a fix provider."""

    dataset_id: str | None = None
    operation: str | None = None
    phase: str | None = None
    output_dir: str | None = None
    recipe_id: str | None = None


class FixProvider(ABC):
    """Base class for dataset fix providers."""

    name = "base"
    dependency_names = ()
    unavailable_message = "The selected fix provider has missing dependencies."

    def available(self):
        """Return whether the provider dependencies are importable."""
        return all(
            importlib.util.find_spec(dependency_name) is not None
            for dependency_name in self.dependency_names
        )

    def require_available(self):
        """Raise a clear error when provider dependencies are missing."""
        if not self.available():
            raise ImportError(self.unavailable_message)

    def prepare(self, ds, *, context=None):
        """Prepare a dataset before the main fix step."""
        return ds

    @abstractmethod
    def apply(self, ds, *, context=None):
        """Apply fixes and return the dataset."""

    def finalise(self, ds, *, context=None):
        """Finalise a dataset after the main fix step."""
        return ds


DatasetFixProvider = FixProvider
