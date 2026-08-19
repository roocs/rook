"""Temporary low-level diagnostics for the CMIP6-decadal concat path."""

import os
from pathlib import Path
import sys

_STATUS_PATH = Path("/proc/self/status")
_FIX_COORDS = ("time", "reftime", "leadtime", "realization")
_FIX_ATTRS = (
    "dataset_id",
    "project_id",
    "startdate",
    "sub_experiment_id",
    "realization_index",
)
_DESCRIPTION_ATTRS = (
    "forcing_description",
    "physics_description",
    "initialization_description",
)


def memory_checkpoint(label, details=None):
    """Write one immediately flushed RSS diagnostic directly to stderr."""
    message = f"[rook-concat-diag] pid={os.getpid()} {_vm_rss()} {label}"
    if details:
        message = f"{message} | {details}"
    print(message, file=sys.stderr, flush=True)


def dataset_signature(label, dataset, *, identity=None):
    """Report properties that identify the CMIP6-decadal recipe result."""
    if not all(hasattr(dataset, name) for name in ("sizes", "variables", "attrs")):
        memory_checkpoint(
            label,
            f"identity={identity} signature=unavailable type={type(dataset).__name__}",
        )
        return
    parts = [f"sizes={dict(dataset.sizes)}"]
    if identity is not None:
        parts.append(f"identity={identity}")

    coordinates = []
    for name in _FIX_COORDS:
        if name not in dataset.variables:
            continue
        variable = dataset[name]
        attributes = _selected_mapping(
            variable.attrs,
            ("standard_name", "long_name", "units", "calendar"),
        )
        encoding = _selected_mapping(variable.encoding, ("calendar", "units", "dtype"))
        coordinates.append(
            f"{name}(dims={variable.dims},dtype={variable.dtype},"
            f"attrs={attributes},encoding={encoding})"
        )
    parts.append(f"fix_vars={';'.join(coordinates) or 'none'}")

    attributes = _selected_mapping(dataset.attrs, _FIX_ATTRS)
    descriptions = ",".join(
        f"{name}={'set' if dataset.attrs.get(name) else 'missing'}"
        for name in _DESCRIPTION_ATTRS
    )
    parts.append(f"attrs={attributes}")
    parts.append(f"descriptions={descriptions}")
    memory_checkpoint(label, " ".join(parts))


def _vm_rss():
    try:
        for line in _STATUS_PATH.read_text().splitlines():
            if line.startswith("VmRSS:"):
                return " ".join(line.split())
    except OSError:
        pass
    return "VmRSS: unavailable"


def _selected_mapping(mapping, names):
    values = []
    for name in names:
        if name not in mapping:
            continue
        value = str(mapping[name]).replace("\n", " ")
        if len(value) > 80:
            value = f"{value[:77]}..."
        values.append(f"{name}={value}")
    return "{" + ",".join(values) + "}"
