"""Generic callback-based concat batching processor."""

from .base import BatchProcessor


class ConcatBatch(BatchProcessor):
    """Slice concat inputs by time and execute one callback per batch."""

    def __init__(self, planner):
        self._planner = planner

    def get_planner(self):
        return self._planner

    def process(self, datasets, process_batch, *, requested_time=None):
        """Lazily slice every dataset and execute the callback sequentially."""
        time = _representative_time(datasets)
        start, end = _closed_time_bounds(requested_time)

        def process_time_batch(batch, index, total):
            selected = _select_time_batch(datasets, batch)
            return process_batch(selected, batch.interval, index, total)

        return super().process(
            time,
            process_time_batch,
            start=start,
            end=end,
        )


def _representative_time(datasets):
    for dataset in datasets:
        if "time" in dataset.coords:
            return dataset.time
    return None


def _closed_time_bounds(time):
    if time is None or getattr(time, "type", None) != "interval":
        return None, None
    start, end = time.get_bounds()
    if not start or not end:
        return None, None
    return start, end


def _select_time_batch(datasets, batch):
    if batch.start is None or batch.end is None:
        return datasets
    time_slice = slice(batch.start, batch.end)
    return [dataset.sel(time=time_slice) for dataset in datasets]
