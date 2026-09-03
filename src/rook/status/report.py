"""Status-check registration and report collection."""

from collections.abc import Iterable
from typing import Any

from rook.__version__ import __version__
from rook.config import DEFAULT_STATUS, ConfigurationError, get_status_config

from .base import StatusCheck
from .disk import DiskStatusCheck
from .filesystem import FilesystemStatusCheck
from .helpers import aggregate_state, make_check, utc_now
from .identification import get_service_identification
from .processes import ProcessDatabaseStatusCheck
from .server import ServerStatusCheck
from .service import ServiceStatusCheck

SCHEMA_VERSION = "1.0"

STATUS_CHECKS: tuple[StatusCheck, ...] = (
    ServiceStatusCheck(),
    ProcessDatabaseStatusCheck(),
    ServerStatusCheck(),
    DiskStatusCheck(),
    FilesystemStatusCheck(),
)


def collect_status(
    status_checks: Iterable[StatusCheck] | None = None,
) -> dict[str, Any]:
    """Collect a complete status report while preserving partial results."""
    measured_at = utc_now()
    try:
        thresholds = get_status_config()
        checks = []
    except ConfigurationError:
        thresholds = DEFAULT_STATUS
        checks = [
            make_check(
                "configuration",
                "red",
                "Status thresholds are invalid.",
                measured_at,
            )
        ]

    if status_checks is None:
        status_checks = STATUS_CHECKS
    for status_check in status_checks:
        checks.extend(
            status_check.run(
                measured_at,
                thresholds,
                timeout_seconds=thresholds["check_timeout_seconds"],
            )
        )

    service = {
        "name": "rook",
        "version": __version__,
        **get_service_identification(),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "state": aggregate_state(check["state"] for check in checks),
        "measured_at": measured_at,
        "service": service,
        "checks": checks,
    }
