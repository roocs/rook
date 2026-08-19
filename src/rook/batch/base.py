"""Common sequential execution support for batching processors."""

from collections.abc import Callable, Iterable, Sequence
from typing import TypeVar

from .planner import TimeBatch

Output = TypeVar("Output")


class BatchProcessor:
    """Execute a completed batch plan sequentially."""

    def execute(
        self,
        batches: Sequence[TimeBatch],
        process_batch: Callable[[TimeBatch, int, int], Iterable[Output]],
    ) -> list[Output]:
        """Finish each callback before starting the next time batch."""
        outputs = []
        total = len(batches)
        for index, batch in enumerate(batches, start=1):
            outputs.extend(process_batch(batch, index, total))
        return outputs
