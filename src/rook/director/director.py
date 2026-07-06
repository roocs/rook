from pywps.app.exceptions import ProcessError

from .execution import execute_request


def execute_planned_request(collection, inputs, runner):
    """Plan a request, execute it when needed, and translate WPS errors."""
    try:
        return execute_request(collection, inputs, runner)
    except Exception as e:
        raise ProcessError(f"{e}")


def wrap_director(collection, inputs, runner):
    """Compatibility alias for callers not yet moved to planner naming."""
    return execute_planned_request(collection, inputs, runner)
