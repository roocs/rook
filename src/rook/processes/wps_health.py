"""Health-check process."""

from pathlib import Path

from pywps import LiteralOutput, Process
from pywps.app.Common import Metadata
from pywps.app.exceptions import ProcessError

from rook.config import ConfigurationError, get_health_readable_files

HEALTHY_RESPONSE = "ROOK_HEALTH_OK"


class HealthCheckError(RuntimeError):
    """Raised when an operational health check fails."""


def run_health_checks():
    """Run operational health checks or raise ``HealthCheckError``."""
    try:
        readable_files = get_health_readable_files()
    except ConfigurationError as exc:
        raise HealthCheckError(str(exc)) from exc

    failures = []
    for name, path in readable_files.items():
        try:
            with Path(path).open("rb") as stream:
                stream.read(1)
        except OSError as exc:
            reason = exc.strerror or exc.__class__.__name__
            failures.append(f"{name}: {reason}")
        except ValueError:
            failures.append(f"{name}: invalid path")

    if failures:
        detail = "; ".join(failures)
        raise HealthCheckError(f"configured files are not readable: {detail}")


class Health(Process):
    """Run the lightweight synchronous Rook health check.

    Request the ``status`` output as ``RawDataOutput``. A healthy response is
    exactly ``ROOK_HEALTH_OK``. Checks should raise ``HealthCheckError`` with a
    concise explanation when unhealthy; the success marker is then omitted.
    The ``.health-check.txt`` file below every project selected in
    ``health.projects`` is opened and read to verify filesystem access.
    """

    def __init__(self):
        outputs = [
            LiteralOutput(
                "status",
                "Status",
                abstract="Rook health status.",
                data_type="string",
            )
        ]

        super().__init__(
            self._handler,
            identifier="health",
            title="Health",
            abstract="Check whether Rook can execute a WPS process.",
            metadata=[Metadata("ROOK", "https://github.com/roocs/rook")],
            version="1.0",
            inputs=[],
            outputs=outputs,
            store_supported=False,
            status_supported=False,
        )

    def _handler(self, _request, response):
        try:
            run_health_checks()
        except HealthCheckError as exc:
            raise ProcessError(f"Health check failed: {exc}") from exc

        response.outputs["status"].data = HEALTHY_RESPONSE
        return response
