"""Configured storage-sentinel status checks."""

from pathlib import Path

from rook.config import get_health_readable_files

from .base import StatusCheck
from .helpers import make_check


class FilesystemStatusCheck(StatusCheck):
    """Report every configured storage sentinel independently."""

    identifier = "filesystem"

    def collect(self, measured_at, _thresholds):
        checks = []
        for name, path in get_health_readable_files().items():
            try:
                with Path(path).open("rb") as stream:
                    stream.read(1)
            except (OSError, ValueError):
                checks.append(
                    make_check(
                        f"filesystem:{name}",
                        "red",
                        "Configured storage is not readable.",
                        measured_at,
                    )
                )
            else:
                checks.append(
                    make_check(
                        f"filesystem:{name}",
                        "green",
                        "Configured storage is readable.",
                        measured_at,
                    )
                )
        if not checks:
            checks.append(
                make_check(
                    self.identifier,
                    "yellow",
                    "No storage sentinels are configured.",
                    measured_at,
                )
            )
        return checks
