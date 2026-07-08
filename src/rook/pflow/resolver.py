"""Resolve requests to processing-flow decisions."""

from collections import OrderedDict

from clisops.project_utils import get_project_name

from rook import config

from .alignment import SubsetAlignmentChecker
from .catalog import dataset_sources_from_search, resolve_catalog_search
from .decisions import ReturnOriginalFiles, RunOperation
from .policies import may_return_original_files, requires_processing
from .sources import CatalogCollection, DirectDataset


def resolve_request_decision(collection, inputs):
    """Return the decision for a request."""
    source = classify_request_source(collection)

    if isinstance(source, DirectDataset):
        return RunOperation(project=source.project)

    return resolve_catalog_collection(source, inputs)


def classify_request_source(collection):
    """Return the request source represented by a collection argument."""
    project = resolve_project(collection)

    if not uses_catalog(project):
        return DirectDataset(collection=collection, project=project)

    return CatalogCollection(collection=collection, project=project)


def resolve_catalog_collection(source, inputs):
    """Return the decision for a catalog collection request."""
    project = source.project
    collection = source.collection

    search_result = resolve_catalog_search(project, collection, inputs)

    if may_return_original_files(project, inputs):
        return original_files_decision(project, search_result)

    if requires_processing(inputs):
        return operation_decision(project, search_result)

    return aligned_subset_decision(project, search_result, inputs)


def resolve_project(collection):
    """Return the project for the first collection entry."""
    return get_project_name(collection[0])


def uses_catalog(project):
    """Return whether requests for a project should use catalog lookup."""
    return bool(config.get_project_config(project).get("use_catalog"))


def original_files_decision(project, search_result, original_file_urls=None):
    """Return a decision that bypasses operation execution."""
    if original_file_urls is None:
        original_file_urls = search_result.download_urls()

    return ReturnOriginalFiles(
        project=project,
        search_result=search_result,
        original_file_urls=original_file_urls,
    )


def operation_decision(project, search_result):
    """Return a decision that runs operation execution."""
    return RunOperation(
        project=project,
        search_result=search_result,
        dataset_sources=dataset_sources_from_search(search_result),
    )


def aligned_subset_decision(project, search_result, inputs):
    """Return an original-file decision when subset bounds align with files."""
    original_file_urls = aligned_original_file_urls(search_result, inputs)

    if original_file_urls is None:
        return operation_decision(project, search_result)

    return original_files_decision(project, search_result, original_file_urls)


def aligned_original_file_urls(search_result, inputs):
    """Return aligned original file URLs, or None when processing is required."""
    required_files = OrderedDict()

    for ds_id, urls in search_result.download_urls().items():
        alignment = SubsetAlignmentChecker(urls, inputs)

        # TODO: don't use original files for atlas data ... need to apply a fix
        # if not alignment.is_aligned or "c3s-cica-atlas" in ds_id:
        if not alignment.is_aligned:
            return None

        required_files[ds_id] = alignment.aligned_files[:]

    return required_files
