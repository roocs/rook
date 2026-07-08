"""Compatibility wrapper for request-decision execution."""

from rook.pflow.execution import (
    collect_original_file_uris,
    execute_decision,
    execute_request,
    prepare_operation_inputs,
    run_operation,
)
from rook.pflow.results import RequestResult


execute_plan = execute_decision

__all__ = [
    "RequestResult",
    "collect_original_file_uris",
    "execute_decision",
    "execute_plan",
    "execute_request",
    "prepare_operation_inputs",
    "run_operation",
]
