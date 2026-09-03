"""Rook service status check."""

import time

import psutil
from pywps import configuration as pywps_configuration

from .base import StatusCheck
from .helpers import make_check


class ServiceStatusCheck(StatusCheck):
    """Report host/worker uptime and configured worker capacity."""

    identifier = "service"

    def collect(self, measured_at, _thresholds):
        process = psutil.Process()
        now = time.time()
        details = {
            "host_uptime_seconds": max(0, round(now - psutil.boot_time())),
            "worker_uptime_seconds": max(0, round(now - process.create_time())),
            "max_processes": int(
                pywps_configuration.get_config_value("server", "maxprocesses")
            ),
            "parallel_processes": int(
                pywps_configuration.get_config_value("server", "parallelprocesses")
            ),
        }
        return [
            make_check(
                self.identifier,
                "green",
                "Rook is responding.",
                measured_at,
                details,
            )
        ]
