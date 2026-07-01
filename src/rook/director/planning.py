"""Plan catalog-backed requests before operation execution."""

from collections import OrderedDict
from dataclasses import dataclass

from clisops.exceptions import InvalidCollection
from clisops.project_utils import get_project_name

from rook import config
from rook.catalog import get_catalog

from .alignment import SubsetAlignmentChecker


@dataclass(frozen=True)
class RequestPlan:
    """Decision values produced before running an operation."""

    project: str
    search_result: object | None = None
    original_file_urls: OrderedDict | None = None

    @property
    def returns_original_files(self):
        """Return whether this request should bypass processing."""
        return self.original_file_urls is not None


def plan_request(collection, inputs):
    """Return the catalog resolution and original-file plan for a request."""
    project = resolve_project(collection)

    if not uses_catalog(project):
        return RequestPlan(project=project)

    search_result = resolve_catalog_search(project, collection, inputs)

    if returns_original_catalog_files(project, inputs):
        return original_files_plan(project, search_result)

    if operation_requires_processing(inputs):
        return operation_plan(project, search_result)

    return aligned_subset_plan(project, search_result, inputs)


def resolve_project(collection):
    """Return the project for the first collection entry."""
    return get_project_name(collection[0])


def uses_catalog(project):
    """Return whether requests for a project should use catalog lookup."""
    return bool(config.get_project_config(project).get("use_catalog"))


def resolve_catalog_search(project, collection, inputs):
    """Resolve a catalog search result and validate all requested collections."""
    catalog = catalog_for(project)
    search_result = catalog.search(
        collection=collection,
        time=inputs.get("time"),
        time_components=inputs.get("time_components"),
    )
    validate_search_result(search_result, collection)
    return search_result


def catalog_for(project):
    """Return the project catalog or raise an invalid-collection error."""
    try:
        return get_catalog(project)
    except Exception:
        raise InvalidCollection()


def validate_search_result(search_result, collection):
    """Raise when the catalog did not match every requested collection."""
    if len(search_result) != len(collection):
        raise InvalidCollection()


def returns_original_catalog_files(project, inputs):
    """Return whether original catalog files should be returned immediately."""
    return requests_original_files(inputs) or project == "c3s-ipcc-atlas"


def original_files_plan(project, search_result, original_file_urls=None):
    """Return a plan that bypasses operation execution."""
    if original_file_urls is None:
        original_file_urls = search_result.download_urls()

    return RequestPlan(
        project=project,
        search_result=search_result,
        original_file_urls=original_file_urls,
    )


def operation_plan(project, search_result):
    """Return a plan that runs operation execution."""
    return RequestPlan(project=project, search_result=search_result)


def aligned_subset_plan(project, search_result, inputs):
    """Return an original-file plan when subset bounds align with files."""
    original_file_urls = aligned_original_file_urls(search_result, inputs)

    if original_file_urls is None:
        return operation_plan(project, search_result)

    return original_files_plan(project, search_result, original_file_urls)


def requests_original_files(inputs):
    """Return whether the caller explicitly requested original files."""
    return bool(inputs.get("original_files"))


def operation_requires_processing(inputs):
    """Return whether the operation changes data and must run."""
    return "dims" in inputs or "freq" in inputs or "grid" in inputs


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
