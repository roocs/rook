"""Processing-flow layer for request decisions and execution."""

from pywps.app.exceptions import ProcessError

from .decisions import InvalidRequest, RequestDecision, ReturnOriginalFiles, RunOperation
from .execution import execute_request
from .resolver import resolve_request_decision
from .results import RequestResult
from .sources import CatalogCollection, DirectDataset, WorkflowFiles


def execute_resolved_request(collection, inputs, runner):
    """Resolve a request, execute it when needed, and translate WPS errors."""
    try:
        return execute_request(collection, inputs, runner)
    except Exception as e:
        raise ProcessError(f"{e}")


__all__ = [
    "CatalogCollection",
    "DirectDataset",
    "InvalidRequest",
    "RequestDecision",
    "RequestResult",
    "ReturnOriginalFiles",
    "RunOperation",
    "WorkflowFiles",
    "execute_resolved_request",
    "resolve_request_decision",
]
