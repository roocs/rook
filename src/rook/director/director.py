from rook.pflow import execute_resolved_request


def execute_planned_request(collection, inputs, runner):
    """Compatibility alias for the old planned-request entry point."""
    return execute_resolved_request(collection, inputs, runner)


def wrap_director(collection, inputs, runner):
    """Compatibility alias for callers not yet moved to pflow naming."""
    return execute_planned_request(collection, inputs, runner)
