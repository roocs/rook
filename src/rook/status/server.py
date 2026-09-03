"""Server resource status check."""

import psutil

from .base import StatusCheck
from .helpers import aggregate_state, make_check, threshold_state


class ServerStatusCheck(StatusCheck):
    """Report server CPU, load, and memory utilization."""

    identifier = "server"

    def collect(self, measured_at, thresholds):
        cpu_count = psutil.cpu_count() or 1
        load = psutil.getloadavg()
        load_percent = load[0] / cpu_count * 100
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        utilization = max(load_percent, cpu_percent)
        state = aggregate_state(
            (
                threshold_state(
                    utilization,
                    thresholds["warning_cpu_percent"],
                    thresholds["failure_cpu_percent"],
                ),
                threshold_state(
                    memory.percent,
                    thresholds["warning_memory_percent"],
                    thresholds["failure_memory_percent"],
                ),
            )
        )
        details = {
            "cpu_count": cpu_count,
            "cpu_percent": round(cpu_percent, 1),
            "load_1m": round(load[0], 2),
            "load_5m": round(load[1], 2),
            "load_15m": round(load[2], 2),
            "load_1m_percent": round(load_percent, 1),
            "memory_percent": round(memory.percent, 1),
            "memory_available_bytes": memory.available,
        }
        return [
            make_check(
                self.identifier,
                state,
                "Server resources measured.",
                measured_at,
                details,
            )
        ]
