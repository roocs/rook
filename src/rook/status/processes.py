"""PyWPS process-database status check."""

from datetime import datetime, timedelta

from pywps.dblog import ProcessInstance, RequestInstance, get_session
from pywps.response.status import WPS_STATUS

from .base import StatusCheck
from .helpers import make_check

RECENT_JOB_SECONDS = 86400


class ProcessDatabaseStatusCheck(StatusCheck):
    """Report queued, active, stale, and recently completed processes."""

    identifier = "processes"

    def collect(self, measured_at, thresholds):
        session = get_session()
        try:
            now = datetime.now()
            stale_before = now - timedelta(seconds=thresholds["stale_job_seconds"])
            recent_after = now - timedelta(seconds=RECENT_JOB_SECONDS)
            stored = session.query(RequestInstance.uuid)
            executions = session.query(ProcessInstance).filter(
                ProcessInstance.operation == "execute",
                ProcessInstance.identifier != "status",
            )
            active = executions.filter(
                ProcessInstance.status.in_(
                    [WPS_STATUS.ACCEPTED, WPS_STATUS.STARTED, WPS_STATUS.PAUSED]
                ),
                ~ProcessInstance.uuid.in_(stored),
            )
            stale = active.filter(ProcessInstance.time_start < stale_before).count()
            details = {
                "queued": stored.count(),
                "running": active.filter(
                    ProcessInstance.time_start >= stale_before
                ).count(),
                "stale": stale,
                "succeeded_24h": executions.filter(
                    ProcessInstance.status == WPS_STATUS.SUCCEEDED,
                    ProcessInstance.time_end >= recent_after,
                ).count(),
                "failed_24h": executions.filter(
                    ProcessInstance.status == WPS_STATUS.FAILED,
                    ProcessInstance.time_end >= recent_after,
                ).count(),
            }
        finally:
            session.close()

        state = "yellow" if stale else "green"
        message = (
            "Stale processes detected."
            if stale
            else "Process database is available."
        )
        return [make_check(self.identifier, state, message, measured_at, details)]
