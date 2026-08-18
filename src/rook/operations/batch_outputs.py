"""Merge small files produced by a time-batched subset operation."""

from collections.abc import Sequence
import logging
from pathlib import Path

from clisops.utils.dataset_utils import open_xr_dataset
from clisops.utils.file_namers import get_file_namer

logger = logging.getLogger(__name__)


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
            "Subset batch output merge failed; returning the original batch outputs"
        )
        return list(outputs)

    logger.info(
        "Merged %d subset batch outputs into %d client-facing file(s)",
        len(outputs),
        len(result),
    )
    return result


def _accept_batch_outputs(outputs: Sequence[str]) -> list[Path]:
    """Accept outputs produced by the preceding subset batch calls."""
    return [Path(output) for output in outputs]


def _plan_merges(
    outputs: Sequence[Path], *, enabled: bool, output_type: str, target_size: int
) -> list[list[Path]]:
    """Group batch outputs using the first batch file as the size estimate."""
    if not enabled or len(outputs) <= 1:
        return [[output] for output in outputs]
    if output_type != "netcdf":
        logger.info("Subset batch output merge skipped for output_type=%s", output_type)
        return [[output] for output in outputs]

    batch_size = max(1, outputs[0].stat().st_size)
    batches_per_merge = max(1, target_size // batch_size)
    return [
        list(outputs[start : start + batches_per_merge])
        for start in range(0, len(outputs), batches_per_merge)
    ]


def _execute_merge_plan(
    groups: Sequence[Sequence[Path]], *, file_namer: str, output_type: str
) -> list[str]:
    """Execute each group in a merge plan in order."""
    namer = get_file_namer(file_namer)()
    result = []
    for group in groups:
        result.extend(
            _merge_group(
                group,
                output_type=output_type,
                namer=namer,
            )
        )
    return result


def _merge_group(group: Sequence[Path], *, output_type: str, namer) -> list[str]:
    if len(group) == 1:
        return [str(group[0])]

    with open_xr_dataset([str(path) for path in group]) as dataset:
        target = group[0].parent / namer.get_file_name(dataset, fmt=output_type)
        dataset.to_netcdf(
            target,
            engine="h5netcdf",
            unlimited_dims=["time"],
        )
    return [str(target)]
