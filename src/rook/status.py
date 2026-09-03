"""Collection and presentation of the public Rook status report."""

from __future__ import annotations

import html
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import psutil
from pywps import configuration as pywps_configuration
from pywps.dblog import ProcessInstance, RequestInstance, get_session
from pywps.response.status import WPS_STATUS

from rook.__version__ import __version__
from rook.config import (
    DEFAULT_STATUS,
    ConfigurationError,
    get_health_readable_files,
    get_status_config,
)

SCHEMA_VERSION = "1.0"
RECENT_JOB_SECONDS = 86400
STATES = ("green", "yellow", "red")


def collect_status() -> dict[str, Any]:
    """Collect a complete status report while preserving partial results."""
    measured_at = _utc_now()
    try:
        thresholds = get_status_config()
        checks = []
    except ConfigurationError:
        thresholds = DEFAULT_STATUS
        checks = [
            _check(
                "configuration",
                "red",
                "Status thresholds are invalid.",
                measured_at,
            )
        ]

    collectors: tuple[tuple[str, Callable[..., list[dict[str, Any]]]], ...] = (
        ("service", _service_checks),
        ("jobs", _job_checks),
        ("server", _server_checks),
        ("disk", _disk_checks),
        ("filesystem", _filesystem_checks),
    )
    for check_id, collector in collectors:
        try:
            checks.extend(collector(measured_at, thresholds))
        except Exception as exc:  # one broken signal must not hide the others
            checks.append(
                _check(
                    check_id,
                    "red",
                    f"Check unavailable ({exc.__class__.__name__}).",
                    measured_at,
                )
            )

    return {
        "schema_version": SCHEMA_VERSION,
        "state": aggregate_state(check["state"] for check in checks),
        "measured_at": measured_at,
        "service": {"name": "rook", "version": __version__},
        "checks": checks,
    }


def aggregate_state(states) -> str:
    """Return the most severe state from an iterable of check states."""
    rank = {state: index for index, state in enumerate(STATES)}
    return max(states, key=rank.__getitem__, default="green")


def render_html(report: dict[str, Any]) -> str:
    """Render the report model as a compact, standalone HTML overview."""
    rows = []
    for check in report["checks"]:
        details = ", ".join(
            f"{key.replace('_', ' ')}: {value}"
            for key, value in check.get("details", {}).items()
        )
        rows.append(
            "<tr>"
            f'<td><span class="state {html.escape(check["state"])}">'
            f'{html.escape(check["state"].upper())}</span></td>'
            f'<th scope="row">{html.escape(check["id"])}</th>'
            f'<td>{html.escape(check["message"])}</td>'
            f"<td>{html.escape(details)}</td>"
            "</tr>"
        )

    title = f'Rook {report["service"]["version"]} status'
    overall_state = html.escape(report["state"])
    measured_at = html.escape(report["measured_at"])
    schema_version = html.escape(report["schema_version"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
body {{
  color: #17202a; font: 16px system-ui, sans-serif; margin: 2rem auto;
  max-width: 75rem; padding: 0 1rem;
}}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{
  border-bottom: 1px solid #d5d8dc; padding: .65rem; text-align: left;
  vertical-align: top;
}}
.state {{
  border-radius: .3rem; color: white; display: inline-block; font-size: .75rem;
  font-weight: 700; padding: .2rem .45rem;
}}
.green {{ background: #18794e; }}
.yellow {{ background: #946800; }}
.red {{ background: #b42318; }}
small {{ color: #566573; }}
</style>
</head>
<body>
<h1>{html.escape(title)}</h1>
<p>Overall state:
<span class="state {overall_state}">{overall_state.upper()}</span></p>
<p><small>Measured at {measured_at}; schema {schema_version}</small></p>
<table><thead><tr>
<th>State</th><th>Check</th><th>Message</th><th>Details</th>
</tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</body>
</html>"""


def _service_checks(measured_at, _thresholds):
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
    return [_check("service", "green", "Rook is responding.", measured_at, details)]


def _job_checks(measured_at, thresholds):
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
    message = "Stale processes detected." if stale else "Process database is available."
    return [_check("processes", state, message, measured_at, details)]


def _server_checks(measured_at, thresholds):
    cpu_count = psutil.cpu_count() or 1
    load = psutil.getloadavg()
    load_percent = load[0] / cpu_count * 100
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    utilization = max(load_percent, cpu_percent)
    state = aggregate_state(
        (
            _threshold_state(
                utilization,
                thresholds["warning_cpu_percent"],
                thresholds["failure_cpu_percent"],
            ),
            _threshold_state(
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
    return [_check("server", state, "Server resources measured.", measured_at, details)]


def _disk_checks(measured_at, thresholds):
    output_path = pywps_configuration.get_config_value("server", "outputpath")
    usage = psutil.disk_usage(output_path)
    state = _threshold_state(
        usage.percent,
        thresholds["warning_disk_percent"],
        thresholds["failure_disk_percent"],
    )
    details = {
        "used_percent": round(usage.percent, 1),
        "free_bytes": usage.free,
        "total_bytes": usage.total,
    }
    return [_check("disk", state, "Output storage measured.", measured_at, details)]


def _filesystem_checks(measured_at, _thresholds):
    checks = []
    for name, path in get_health_readable_files().items():
        try:
            with Path(path).open("rb") as stream:
                stream.read(1)
        except (OSError, ValueError):
            checks.append(
                _check(
                    f"filesystem:{name}",
                    "red",
                    "Configured storage is not readable.",
                    measured_at,
                )
            )
        else:
            checks.append(
                _check(
                    f"filesystem:{name}",
                    "green",
                    "Configured storage is readable.",
                    measured_at,
                )
            )
    if not checks:
        checks.append(
            _check(
                "filesystem",
                "yellow",
                "No storage sentinels are configured.",
                measured_at,
            )
        )
    return checks


def _threshold_state(value, warning, failure):
    if value >= failure:
        return "red"
    if value >= warning:
        return "yellow"
    return "green"


def _check(check_id, state, message, measured_at, details=None):
    check = {
        "id": check_id,
        "state": state,
        "message": message,
        "measured_at": measured_at,
    }
    if details is not None:
        check["details"] = details
    return check


def _utc_now():
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
