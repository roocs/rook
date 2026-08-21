"""Concat-specific time-batch planning."""

from .base import (
    BaseBatchPlanner,
    TimeBounds,
    estimate_timesteps_per_year,
    timestep_batches,
)


class ConcatBatchPlanner(BaseBatchPlanner):
    """Plan concat batches from a representative time coordinate."""

    def plan(self, time, requested_time=None, *, bytes_per_timestep=None):
        bounds = _requested_bounds(requested_time)
        target_timesteps = self.effective_target_timesteps(bytes_per_timestep)
        if (
            time is not None
            and getattr(time, "size", 0) > 0
            and target_timesteps < estimate_timesteps_per_year(time, time.dt.calendar)
        ):
            return timestep_batches(time, bounds, target_timesteps)
        return self._plan(
            time,
            bounds,
            target_timesteps=target_timesteps,
        )


def _requested_bounds(time):
    if time is None or getattr(time, "type", None) != "interval":
        return None
    start, end = time.get_bounds()
    if not start or not end:
        return None
    return TimeBounds(start, end)
