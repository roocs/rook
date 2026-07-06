"""Plan requests before operation execution."""

from collections import OrderedDict
from dataclasses import dataclass

from clisops.exceptions import InvalidCollection
from clisops.project_utils import get_project_name
from clisops.utils.file_utils import FileMapper

from rook import config
from rook.catalog import get_catalog

from .alignment import SubsetAlignmentChecker


ORIGINAL_FILE_PROJECTS = frozenset({"c3s-ipcc-atlas"})
PROCESSING_REQUIRED_INPUTS = frozenset({"dims", "freq", "grid"})


@dataclass(frozen=True)
class CatalogCollection:
    """A request source that should be resolved through a project catalog."""

    collection: list[str]
    project: str


@dataclass(frozen=True)
class DirectDataset:
    """A request source that should be processed directly without catalog lookup."""

    collection: list[str]
    project: str


@dataclass(frozen=True)
class WorkflowFiles:
    """Files produced by an earlier workflow step."""

    files: list[str]


@dataclass(frozen=True)
class ReturnOriginalFiles:
    """Decision to return catalog file URLs without running an operation."""

    project: str
    search_result: object | None = None
    original_file_urls: OrderedDict | None = None

    @property
    def returns_original_files(self):
        """Return whether this request should bypass processing."""
        return True

    @property
    def dataset_sources(self):
        """Return no prepared operation sources for original-file responses."""
        return ()


@dataclass(frozen=True)
class RunOperation:
    """Decision to run an operation on the requested or prepared sources."""

    project: str
    search_result: object | None = None
    dataset_sources: tuple[FileMapper, ...] = ()

    @property
    def returns_original_files(self):
        """Return whether this request should bypass processing."""
        return False

    @property
    def original_file_urls(self):
        """Return no original file URLs for operation responses."""
        return None


@dataclass(frozen=True)
class InvalidRequest:
    """Decision value reserved for explicit invalid-request outcomes."""

    message: str


RequestDecision = InvalidRequest | ReturnOriginalFiles | RunOperation
RequestPlan = RequestDecision


def plan_request(collection, inputs):
    """Return the decision for a request."""
    source = classify_request_source(collection)

    if isinstance(source, DirectDataset):
        return RunOperation(project=source.project)

    return plan_catalog_collection(source, inputs)


def classify_request_source(collection):
    """Return the request source represented by a collection argument."""
    project = resolve_project(collection)

    if not uses_catalog(project):
        return DirectDataset(collection=collection, project=project)

    return CatalogCollection(collection=collection, project=project)


def plan_catalog_collection(source, inputs):
    """Return the decision for a catalog collection request."""
    project = source.project
    collection = source.collection

    search_result = resolve_catalog_search(project, collection, inputs)

    if may_return_original_files(project, inputs):
        return original_files_plan(project, search_result)

    if requires_processing(inputs):
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


def may_return_original_files(project, inputs):
    """Return whether catalog data may be returned without processing."""
    return requests_original_files(inputs) or project_returns_original_files(project)


def original_files_plan(project, search_result, original_file_urls=None):
    """Return a plan that bypasses operation execution."""
    if original_file_urls is None:
        original_file_urls = search_result.download_urls()

    return ReturnOriginalFiles(
        project=project,
        search_result=search_result,
        original_file_urls=original_file_urls,
    )


def operation_plan(project, search_result):
    """Return a plan that runs operation execution."""
    return RunOperation(
        project=project,
        search_result=search_result,
        dataset_sources=dataset_sources_from_search(search_result),
    )


def aligned_subset_plan(project, search_result, inputs):
    """Return an original-file plan when subset bounds align with files."""
    original_file_urls = aligned_original_file_urls(search_result, inputs)

    if original_file_urls is None:
        return operation_plan(project, search_result)

    return original_files_plan(project, search_result, original_file_urls)


def requests_original_files(inputs):
    """Return whether the caller explicitly requested original files."""
    return bool(inputs.get("original_files"))


def project_returns_original_files(project):
    """Return whether a project currently bypasses processing by policy."""
    return project in ORIGINAL_FILE_PROJECTS


def requires_processing(inputs):
    """Return whether the requested operation changes data and must run."""
    return has_processing_required_input(inputs)


def has_processing_required_input(inputs):
    """Return whether current request parameters imply changed output data.

    This preserves the existing operation detection rule while keeping the
    hard-coded parameter names out of the main planning flow.
    """
    return bool(PROCESSING_REQUIRED_INPUTS.intersection(inputs))


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


def dataset_sources_from_search(search_result):
    """Return file mappers for catalog-resolved operation inputs."""
    dataset_sources = []

    for ds_id, file_uris in search_result.files().items():
        file_mapper = FileMapper(file_uris)
        file_mapper.dataset_id = ds_id
        dataset_sources.append(file_mapper)

    return tuple(dataset_sources)
