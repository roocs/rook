"""Base contract for independently executable status checks."""

from abc import ABC, abstractmethod
from queue import Queue
from threading import Thread

from .helpers import make_check


class StatusCheck(ABC):
    """One independently executable group of status signals."""

    identifier: str

    def run(self, measured_at, thresholds, timeout_seconds):
        """Collect results, returning red on failure or timeout."""
        outcome = Queue(maxsize=1)

        def collect():
            try:
                results = list(self.collect(measured_at, thresholds))
                if not results:
                    raise ValueError("status check returned no results")
            except Exception as exc:  # one broken signal must not hide the others
                results = [
                    make_check(
                        self.identifier,
                        "red",
                        f"Check unavailable ({exc.__class__.__name__}).",
                        measured_at,
                    )
                ]
            outcome.put(results)

        worker = Thread(
            target=collect,
            name=f"rook-status-{self.identifier}",
            daemon=True,
        )
        worker.start()
        worker.join(timeout_seconds)
        if worker.is_alive():
            return [
                make_check(
                    self.identifier,
                    "red",
                    "Check timed out.",
                    measured_at,
                    {"timeout_seconds": timeout_seconds},
                )
            ]
        return outcome.get_nowait()

    @abstractmethod
    def collect(self, measured_at, thresholds):
        """Return one or more public status results."""
