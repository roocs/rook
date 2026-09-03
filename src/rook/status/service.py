"""Rook service status check."""

from datetime import datetime

import psutil
from pywps import configuration as pywps_configuration

from .base import StatusCheck
from .helpers import make_check


class ServiceStatusCheck(StatusCheck):
    """Report service uptime and configured worker capacity."""

    identifier = "service"

    def collect(self, measured_at, _thresholds):
        process = psutil.Process()
        uptime = max(0, round(datetime.now().timestamp() - process.create_time()))
        details = {
            "uptime_seconds": uptime,
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
