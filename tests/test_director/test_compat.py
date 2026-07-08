from rook.director import execute_planned_request, wrap_director
from rook.director.planning import WorkflowFiles, plan_request
from rook.pflow import execute_resolved_request
from rook.pflow.resolver import resolve_request_decision


def test_director_namespace_keeps_compatibility_aliases():
    assert execute_planned_request is not None
    assert wrap_director is not None
    assert plan_request is not None
    assert WorkflowFiles is not None
    assert execute_resolved_request is not None
    assert resolve_request_decision is not None
