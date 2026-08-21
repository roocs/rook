"""Merge small files produced by time-batched operations."""

from collections.abc import Sequence
import logging
from math import ceil, prod
from pathlib import Path

import dask
from clisops.utils.dataset_utils import open_xr_dataset
from clisops.utils.file_namers import get_file_namer

logger = logging.getLogger(__name__)

MERGE_CHUNK_BYTES = 64 * 1024**2


def merge_batch_outputs(
    outputs: Sequence[str],
    *,
    file_namer: str,
    output_type: str,
    merge_outputs: bool,
    merge_target_bytes: int,
    max_output_bytes: int,
) -> list[str]:
    """Return merged files for small chronological NetCDF batch groups."""
    batch_outputs = _accept_batch_outputs(outputs)
    try:
        merge_plan = _plan_merges(
            batch_outputs,
            enabled=merge_outputs,
            output_type=output_type,
            target_size=min(merge_target_bytes, max_output_bytes),
        )
        result = _execute_merge_plan(
            merge_plan,
            file_namer=file_namer,
            output_type=output_type,
        )
    except Exception:
        logger.exception(
            "Batch output merge failed; returning the original batch outputs"
        )
        return list(outputs)

    logger.info(
        "Merged %d batch outputs into %d client-facing file(s)",
        len(outputs),
        len(result),
    )
    return result


def _accept_batch_outputs(outputs: Sequence[str]) -> list[Path]:
    return [Path(output) for output in outputs]


def _plan_merges(
    outputs: Sequence[Path], *, enabled: bool, output_type: str, target_size: int
) -> list[list[Path]]:
    if not enabled or len(outputs) <= 1:
        return [[output] for output in outputs]
    if output_type != "netcdf":
        logger.info("Batch output merge skipped for output_type=%s", output_type)
        return [[output] for output in outputs]

    groups = []
    group = []
    group_size = 0
    for output in outputs:
        output_size = max(1, output.stat().st_size)
        if group and group_size + output_size > target_size:
            groups.append(group)
            group = []
            group_size = 0
        group.append(output)
        group_size += output_size
    if group:
        groups.append(group)
    return groups


def _execute_merge_plan(
    groups: Sequence[Sequence[Path]], *, file_namer: str, output_type: str
) -> list[str]:
    namer = get_file_namer(file_namer)()
    result = []
    for group in groups:
        result.extend(_merge_group(group, output_type=output_type, namer=namer))
    return result


def _merge_group(group: Sequence[Path], *, output_type: str, namer) -> list[str]:
    if len(group) == 1:
        return [str(group[0])]

    # Xarray otherwise creates one Dask chunk per input file. A large compressed
    # batch could therefore be decoded into memory as a single task. Explicit
    # chunks also work for decoded CF-time bounds, whose object dtype prevents
    # Dask auto-chunking.
    chunks = _bounded_chunks(group[0])
    with dask.config.set(scheduler="single-threaded"):
        with open_xr_dataset([str(path) for path in group], chunks=chunks) as dataset:
            target = group[0].parent / namer.get_file_name(dataset, fmt=output_type)
            dataset.to_netcdf(target, engine="h5netcdf", unlimited_dims=["time"])
    return [str(target)]


def _bounded_chunks(
    path: Path, target_bytes: int = MERGE_CHUNK_BYTES
) -> dict[str, int]:
    """Plan decoded chunks no larger than the merge task target."""
    with open_xr_dataset(str(path)) as dataset:
        chunks = dict(dataset.sizes)

        variables = sorted(
            dataset.variables.values(),
            key=lambda variable: variable.dtype.itemsize
            * prod(chunks[dim] for dim in variable.dims),
            reverse=True,
        )
        for variable in variables:
            while (
                variable.dtype.itemsize * prod(chunks[dim] for dim in variable.dims)
                > target_bytes
            ):
                candidates = [dim for dim in variable.dims if chunks[dim] > 1]
                if not candidates:
                    break
                dimension = max(candidates, key=chunks.__getitem__)
                chunks[dimension] = ceil(chunks[dimension] / 2)
    return chunks
