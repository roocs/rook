"""Resolve requests to processing-flow decisions."""

from collections import OrderedDict
import re

from clisops.project_utils import get_project_name

from rook import config

from .alignment import SubsetAlignmentChecker
from .catalog import dataset_sources_from_search, resolve_catalog_search
from .decisions import ReturnOriginalFiles, RunOperation
from .policies import may_return_original_files, requires_processing
from .sources import CatalogCollection, DirectDataset


def resolve_request_decision(collection, inputs, allow_aligned_original_files=False):
    """Return the decision for a request."""
    source = classify_request_source(collection)

    if isinstance(source, DirectDataset):
        return RunOperation(project=source.project)

    return resolve_catalog_collection(
        source,
        inputs,
        allow_aligned_original_files=allow_aligned_original_files,
    )


def classify_request_source(collection):
    """Return the request source represented by a collection argument."""
    project = resolve_project(collection)

    if not uses_catalog(project):
        return DirectDataset(collection=collection, project=project)

    return CatalogCollection(collection=collection, project=project)


def resolve_catalog_collection(source, inputs, allow_aligned_original_files=False):
    """Return the decision for a catalog collection request."""
    project = source.project
    collection = source.collection

    search_result = resolve_catalog_search(project, collection, inputs)

    if may_return_original_files(project, inputs):
        return original_files_decision(project, search_result)

    if requires_processing(inputs):
        return operation_decision(project, search_result)

    if not allow_aligned_original_files:
        return operation_decision(project, search_result)

    return subset_original_files_decision(project, search_result, inputs)


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


def subset_original_files_decision(project, search_result, inputs):
    """Prefer original files for exact or temporal-only subset requests."""
    original_file_urls = aligned_original_file_urls(search_result, inputs)

    if original_file_urls is not None:
        return original_files_decision(project, search_result, original_file_urls)

    # The catalog has already limited these files to those overlapping `time`.
    # Returning them may include extra timesteps at file boundaries, but avoids
    # an expensive temporal-only subset that can exhaust worker memory.
    if is_high_frequency_temporal_subset(search_result, inputs):
        return original_files_decision(project, search_result)

    return operation_decision(project, search_result)


def is_high_frequency_temporal_subset(search_result, inputs):
    """Return whether a daily/sub-daily subset may over-include only time."""
    is_temporal_only = bool(inputs.get("time")) and not any(
        inputs.get(key) for key in ("time_components", "area", "level", "shape")
    )
    if not is_temporal_only:
        return False

    dataset_ids = search_result.download_urls()
    return bool(dataset_ids) and all(
        has_daily_or_subdaily_frequency(dataset_id) for dataset_id in dataset_ids
    )


def has_daily_or_subdaily_frequency(dataset_id):
    """Return whether a dataset identifier contains a daily-or-finer frequency."""
    for component in dataset_id.lower().split("."):
        if component.endswith("day"):
            return True
        if re.fullmatch(r"[a-z]*\d*hr[a-z]*", component):
            return True
        if "hour" in component:
            return True
    return False


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
