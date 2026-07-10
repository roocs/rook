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

    def missing_dependencies(self):
        """Return provider dependencies that are not importable."""
        return [
            dependency_name
            for dependency_name in self.dependency_names
            if importlib.util.find_spec(dependency_name) is None
        ]

    def available(self):
        """Return whether the provider dependencies are importable."""
        return not self.missing_dependencies()

    def require_available(self):
        """Raise a clear error when provider dependencies are missing."""
        missing = self.missing_dependencies()
        if missing:
            missing_names = ", ".join(missing)
            raise ImportError(f"{self.unavailable_message} Missing: {missing_names}.")

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
