"""Compatibility wrapper for request-decision resolution."""

from rook.pflow.alignment import SubsetAlignmentChecker
from rook.pflow.catalog import (
    catalog_for,
    dataset_sources_from_search,
    get_catalog,
    resolve_catalog_search,
    validate_search_result,
)
from rook.pflow.decisions import (
    InvalidRequest,
    RequestDecision,
    ReturnOriginalFiles,
    RunOperation,
)
from rook.pflow.policies import (
    ORIGINAL_FILE_PROJECTS,
    PROCESSING_REQUIRED_INPUTS,
    has_processing_required_input,
    may_return_original_files,
    project_returns_original_files,
    requests_original_files,
    requires_processing,
)
from rook.pflow.resolver import (
    aligned_original_file_urls,
    aligned_subset_decision,
    classify_request_source,
    operation_decision,
    original_files_decision,
    resolve_catalog_collection,
    resolve_project,
    resolve_request_decision,
    uses_catalog,
)
from rook.pflow.sources import CatalogCollection, DirectDataset, WorkflowFiles


RequestPlan = RequestDecision
plan_request = resolve_request_decision
plan_catalog_collection = resolve_catalog_collection
original_files_plan = original_files_decision
operation_plan = operation_decision
aligned_subset_plan = aligned_subset_decision

__all__ = [
    "ORIGINAL_FILE_PROJECTS",
    "PROCESSING_REQUIRED_INPUTS",
    "CatalogCollection",
    "DirectDataset",
    "InvalidRequest",
    "RequestDecision",
    "RequestPlan",
    "ReturnOriginalFiles",
    "RunOperation",
    "SubsetAlignmentChecker",
    "WorkflowFiles",
    "aligned_original_file_urls",
    "aligned_subset_decision",
    "aligned_subset_plan",
    "catalog_for",
    "classify_request_source",
    "dataset_sources_from_search",
    "get_catalog",
    "has_processing_required_input",
    "may_return_original_files",
    "operation_decision",
    "operation_plan",
    "original_files_decision",
    "original_files_plan",
    "plan_catalog_collection",
    "plan_request",
    "project_returns_original_files",
    "requests_original_files",
    "requires_processing",
    "resolve_catalog_collection",
    "resolve_catalog_search",
    "resolve_project",
    "resolve_request_decision",
    "uses_catalog",
    "validate_search_result",
]
