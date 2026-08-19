"""Normalise datasets and hold operation results."""

from collections import OrderedDict
import pathlib

from clisops.utils.dataset_utils import open_xr_dataset
from loguru import logger
import psutil
import xarray as xr

from rook.io.datasets import open_dataset


def normalise(collection):
    """Open input collections."""
    logger.info(f"Working on datasets: {collection}")
    norm_collection = OrderedDict()

    for source in collection:
        ds = open_dataset(source)
        norm_collection[source.key] = ds

    return norm_collection


def keep_dataset(ds):
    """Return a dataset unchanged."""
    return ds


def normalise_file_groups(
    collection,
    *,
    prepare_dataset=None,
    concat_dim="time",
    opener=open_xr_dataset,
):
    """Open grouped file paths and concatenate each group."""
    norm_collection = OrderedDict()

    if prepare_dataset is None:
        prepare_dataset = keep_dataset

    for dset, file_paths in collection.items():
        file_paths = tuple(file_paths)
        logger.info(
            "Normalizing group={} files={} rss={}",
            dset,
            len(file_paths),
            _rss_size(),
        )
        datasets = []
        for index, file in enumerate(file_paths, start=1):
            dataset = prepare_dataset(opener(file))
            datasets.append(dataset)
            logger.info(
                "Normalized input group={} file={}/{} {}",
                dset,
                index,
                len(file_paths),
                _dataset_summary(dataset),
            )

        logger.info("Concatenating group={} rss={}", dset, _rss_size())
        normalized = xr.concat(
            datasets,
            dim=concat_dim,
            data_vars="minimal",
            coords="minimal",
            compat="override",
            join="exact",
        )
        norm_collection[dset] = normalized
        logger.info(
            "Normalized group={} rss={} {}",
            dset,
            _rss_size(),
            _dataset_summary(normalized),
        )

    return norm_collection


def _rss_size():
    rss = psutil.Process().memory_info().rss
    return f"{rss / (1024**2):.1f}MiB"


def _dataset_summary(dataset, variable_limit=8):
    sizes = dict(dataset.sizes)
    variables = list(dataset.data_vars.items())
    summaries = [
        f"{name}[{_backing_type(variable.variable._data)};{_chunk_summary(variable)}]"
        for name, variable in variables[:variable_limit]
    ]
    if len(variables) > variable_limit:
        summaries.append(f"+{len(variables) - variable_limit} more")
    return f"sizes={sizes} variables={','.join(summaries) or 'none'}"


def _backing_type(data):
    data = _unwrap_backing_array(data)
    cls = type(data)
    module = cls.__module__
    if module.startswith("dask") or hasattr(data, "__dask_graph__"):
        family = "dask"
    elif module.startswith("numpy"):
        family = "numpy"
    else:
        family = module.split(".", 1)[0]
    return f"{family}:{cls.__name__}"


def _unwrap_backing_array(data):
    """Inspect Xarray wrappers without coercing their lazy backing arrays."""
    seen = set()
    while type(data).__module__.startswith("xarray") and hasattr(data, "array"):
        if id(data) in seen:
            break
        seen.add(id(data))
        data = data.array
    return data


def _chunk_summary(variable):
    if variable.chunks is None:
        return "chunks=none"

    dimensions = []
    for dim, chunks in zip(variable.dims, variable.chunks):
        if not chunks:
            dimensions.append(f"{dim}:empty")
            continue
        minimum = min(chunks)
        maximum = max(chunks)
        size = str(minimum) if minimum == maximum else f"{minimum}-{maximum}"
        dimensions.append(f"{dim}:{len(chunks)}x{size}")
    return f"chunks={';'.join(dimensions)}"


class ResultSet:
    """A class to hold the results from an operation."""

    def __init__(self, inputs=None):  # noqa: D107
        self._results = OrderedDict()
        self.metadata = {"inputs": inputs, "process": "something", "version": 0.1}
        self.file_uris = []

    def add(self, dset, result):
        """Add outputs with ds id key and collect file URIs."""
        self._results[dset] = result

        for item in result:
            if isinstance(item, str) and (
                pathlib.Path(item).is_file() or item.startswith("https")
            ):
                self.file_uris.append(item)
