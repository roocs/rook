"""Output-filesystem capacity status check."""

import psutil
from pywps import configuration as pywps_configuration

from .base import StatusCheck
from .helpers import make_check, threshold_state


class DiskStatusCheck(StatusCheck):
    """Report output-filesystem capacity."""

    identifier = "disk"

    def collect(self, measured_at, thresholds):
        output_path = pywps_configuration.get_config_value("server", "outputpath")
        usage = psutil.disk_usage(output_path)
        state = threshold_state(
            usage.percent,
            thresholds["warning_disk_percent"],
            thresholds["failure_disk_percent"],
        )
        details = {
            "used_percent": round(usage.percent, 1),
            "free_bytes": usage.free,
            "total_bytes": usage.total,
        }
        return [
            make_check(
                self.identifier,
                state,
                "Output storage measured.",
                measured_at,
                details,
            )
        ]
