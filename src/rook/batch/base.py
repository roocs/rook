"""Common sequential execution support for batching processors."""

from collections.abc import Callable, Iterable, Sequence
from typing import TypeVar

from .planner import TimeBatch

Output = TypeVar("Output")


class BatchProcessor:
    """Plan and execute time batches sequentially."""

    def get_planner(self):
        """Return the time-batch planner used by this processor."""
        raise NotImplementedError

    def plan(self, time, *, start=None, end=None, calendar=None):
        """Plan batches through the processor's shared planner."""
        return self.get_planner().plan(
            time,
            start=start,
            end=end,
            calendar=calendar,
        )

    def process(
        self,
        time,
        process_batch: Callable[[TimeBatch, int, int], Iterable[Output]],
        *,
        start=None,
        end=None,
        calendar=None,
    ) -> list[Output]:
        """Plan and execute batches, completing each callback in sequence."""
        batches = self.plan(time, start=start, end=end, calendar=calendar)
        return self.execute(batches, process_batch)

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
