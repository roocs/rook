"""Consolidate file paths for each dataset in a collection."""

import re
from pathlib import Path

from clisops.exceptions import InvalidCollection
from clisops.project_utils import derive_ds_id, dset_to_filepaths, get_project_name
from clisops.utils.dataset_utils import open_xr_dataset
from clisops.utils.file_utils import FileMapper
from loguru import logger

from rook.catalog import get_catalog
from rook.io.datasets import (
    DatasetFormat,
    DatasetSource,
    Transport,
    detect_format,
    detect_transport,
)


def _bypasses_catalog(value):
    """Return whether a direct source should skip project resolution."""
    source = DatasetSource(dataset_id=None, paths=value)
    return (
        detect_format(source) is not DatasetFormat.NETCDF
        or detect_transport(source) is Transport.S3
    )


def _resolve_file_source(dset, time_param):
    """Resolve a mapped file input or a dataset without a Rook catalog."""
    file_paths = dset_to_filepaths(dset, force=True)

    if time_param:
        file_paths = get_files_matching_time_range(time_param, file_paths)

    if not file_paths:
        raise Exception(f"No files found in given time range for {dset}")

    dataset_id = (
        getattr(dset, "dataset_id", None) if isinstance(dset, FileMapper) else str(dset)
    )
    return DatasetSource(dataset_id=dataset_id, paths=file_paths)


def _resolve_catalog_sources(dset, catalog, time_param):
    """Resolve one catalog input into normalized dataset sources."""
    dataset_id = derive_ds_id(dset)
    result = catalog.search(collection=dataset_id, time=time_param)

    if len(result) == 0:
        result = catalog.search(collection=dataset_id, time=None)
        if len(result) > 0:
            raise Exception(f"No files found in given time range for {dset}")
        raise InvalidCollection(f"{dset} is not in the list of available data.")

    logger.info(f"Found {len(result)} files")
    return tuple(
        DatasetSource(dataset_id=matched_id, paths=paths)
        for matched_id, paths in result.files().items()
    )


def _catalog_for(dset, catalogs):
    """Return a cached project catalog for a dataset input."""
    project = get_project_name(dset)
    if project not in catalogs:
        catalogs[project] = get_catalog(project)
    return catalogs[project]


def to_year(time_string):
    """Return the year in a time string as an integer."""
    return int(time_string.split("-")[0])


def get_year(value, default):
    """Get a year from a datetime string."""
    if value:
        return to_year(value)
    return default


def get_years_from_file(fpath):
    """Attempt to extract years from file name or file time axis."""
    time_comps = Path(fpath).stem.split("_")[-1].split("-")
    years = {int(tm[:4]) for tm in time_comps if re.match(r"^\d{4,}", tm)}

    if len(years) > 1:
        years = set(range(min(years), max(years) + 1))

    if not years:
        ds = open_xr_dataset(fpath)
        if hasattr(ds, "time"):
            years = {int(yr) for yr in ds.time.dt.year}

    return years


def get_files_matching_time_range(time_param, file_paths):
    """Filter files whose years intersect requested time range."""
    if time_param.type == "none":
        return file_paths

    logger.info(f"Testing {len(file_paths)} files in time range: ...")
    files_in_time_range = []

    if time_param.type == "interval":
        tp_start, tp_end = time_param.get_bounds()
        req_start_year = get_year(tp_start, default=-99999999)
        req_end_year = get_year(tp_end, default=999999999)

        for fpath in file_paths:
            years = get_years_from_file(fpath)
            if min(years) <= req_end_year and max(years) >= req_start_year:
                files_in_time_range.append(fpath)

    elif time_param.type == "series":
        req_years = {to_year(tm) for tm in time_param.asdict().get("time_values", [])}

        for fpath in file_paths:
            years = get_years_from_file(fpath)
            if req_years.intersection(years):
                files_in_time_range.append(fpath)

    logger.info(f"Kept {len(files_in_time_range)} files")
    return files_in_time_range


def consolidate(collection, **kwargs):
    """Find file paths relating to each input dataset."""
    collection = collection.value
    if isinstance(collection, str):
        collection = [collection]

    sources = []
    time_param = kwargs.get("time")
    catalogs = {}

    for dset in collection:
        if isinstance(dset, DatasetSource):
            sources.append(dset)
            continue

        if not isinstance(dset, FileMapper) and _bypasses_catalog(dset):
            sources.append(DatasetSource(dataset_id=None, paths=dset))
            continue

        catalog = None if isinstance(dset, FileMapper) else _catalog_for(dset, catalogs)
        if catalog:
            sources.extend(_resolve_catalog_sources(dset, catalog, time_param))
        else:
            sources.append(_resolve_file_source(dset, time_param))

    return tuple(sources)
