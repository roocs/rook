"""Abstract processing-flow vocabulary."""

from abc import ABC, abstractmethod


class RequestSource:
    """Normalized source for a request."""


class RequestDecision(ABC):
    """One decision about how a request should be handled."""

    @property
    @abstractmethod
    def returns_original_files(self):
        """Return whether the decision bypasses operation execution."""


class RequestResolver(ABC):
    """Turns raw request inputs into one request decision."""

    @abstractmethod
    def resolve(self, collection, inputs):
        """Return one request decision."""


class DecisionExecutor(ABC):
    """Executes one request decision."""

    @abstractmethod
    def execute(self, decision, inputs, runner):
        """Return output URIs for a request decision."""


class RequestPolicy:
    """Optional base for small context-specific request policies."""
