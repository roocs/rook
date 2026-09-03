"""Base contract for independently executable status checks."""

from abc import ABC, abstractmethod

from .helpers import make_check


class StatusCheck(ABC):
    """One independently executable group of status signals."""

    identifier: str

    def run(self, measured_at, thresholds):
        """Collect results, converting an unexpected failure into one result."""
        try:
            return self.collect(measured_at, thresholds)
        except Exception as exc:  # one broken signal must not hide the others
            return [
                make_check(
                    self.identifier,
                    "red",
                    f"Check unavailable ({exc.__class__.__name__}).",
                    measured_at,
                )
            ]

    @abstractmethod
    def collect(self, measured_at, thresholds):
        """Return one or more public status results."""
