"""Catalog lookup, validation, and dataset-source preparation."""

from clisops.exceptions import InvalidCollection

from rook.catalog import get_catalog
from rook.io.datasets import DatasetSource


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


def dataset_sources_from_search(search_result):
    """Return normalized sources for catalog-resolved operation inputs."""
    return tuple(DatasetSource(dataset_id=ds_id, paths=file_uris) for ds_id, file_uris in search_result.files().items())
