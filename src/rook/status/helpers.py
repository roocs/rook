"""Shared helpers for status checks and reports."""

from datetime import UTC, datetime

STATES = ("green", "yellow", "red")


def aggregate_state(states) -> str:
    """Return the most severe state from an iterable of check states."""
    rank = {state: index for index, state in enumerate(STATES)}
    return max(states, key=rank.__getitem__, default="green")


def threshold_state(value, warning, failure):
    """Map a measured value and two thresholds to a traffic-light state."""
    if value >= failure:
        return "red"
    if value >= warning:
        return "yellow"
    return "green"


def make_check(check_id, state, message, measured_at, details=None):
    """Build one serializable public check result."""
    check = {
        "id": check_id,
        "state": state,
        "message": message,
        "measured_at": measured_at,
    }
    if details is not None:
        check["details"] = details
    return check


def utc_now():
    """Return the current UTC time in the status-report representation."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
