"""Subset-specific time-batch planning."""

from math import floor

from .base import BaseBatchPlanner


MEMORY_AMPLIFICATION_FACTOR = 2


class SubsetBatchPlanner(BaseBatchPlanner):
    """Plan batches for a subset request with closed requested bounds."""

    def __init__(self, *, memory_limit_bytes=None, **kwargs):
        super().__init__(**kwargs)
        self.memory_limit_bytes = memory_limit_bytes

    def memory_target_timesteps(self, bytes_per_timestep):
        """Estimate timesteps fitting the memory aim with writer headroom."""
        if self.memory_limit_bytes is None or not bytes_per_timestep:
            return None
        estimated_process_bytes_per_timestep = self.estimated_process_bytes(
            1, bytes_per_timestep
        )
        return max(
            1,
            floor(self.memory_limit_bytes / estimated_process_bytes_per_timestep),
        )

    @staticmethod
    def estimated_process_bytes(timesteps, bytes_per_timestep):
        """Estimate peak process bytes for a decoded temporal payload."""
        if not bytes_per_timestep:
            return None
        return timesteps * bytes_per_timestep * MEMORY_AMPLIFICATION_FACTOR

    def effective_target_timesteps(self, bytes_per_timestep=None):
        """Return the stricter configured timestep or estimated memory target."""
        memory_target = self.memory_target_timesteps(bytes_per_timestep)
        if memory_target is None:
            return self.target_timesteps
        return min(self.target_timesteps, memory_target)

    def plan(self, time, bounds, *, bytes_per_timestep=None):
        if bounds.start is None or bounds.end is None:
            return []
        return self._plan(
            time,
            bounds,
            target_timesteps=self.effective_target_timesteps(bytes_per_timestep),
        )
