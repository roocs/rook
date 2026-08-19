"""Concise diagnostics for lazy Xarray datasets and variables."""

from .memory import memory_checkpoint


def dataset_summary(dataset, variable_limit=8):
    """Return sizes, backing types, and compact chunk details."""
    sizes = dict(dataset.sizes)
    variables = list(dataset.data_vars.items())
    summaries = [
        f"{name}[{_backing_type(variable.variable._data)};{_chunk_summary(variable)}]"
        for name, variable in variables[:variable_limit]
    ]
    if len(variables) > variable_limit:
        summaries.append(f"+{len(variables) - variable_limit} more")
    return f"sizes={sizes} variables={','.join(summaries) or 'none'}"


def dataset_signature(
    label,
    dataset,
    *,
    identity=None,
    coordinate_names=("time",),
    attribute_names=("dataset_id", "project_id"),
    presence_attributes=(),
):
    """Report selected coordinates and attributes without reading array values."""
    if not all(hasattr(dataset, name) for name in ("sizes", "variables", "attrs")):
        memory_checkpoint(
            label,
            f"identity={identity} signature=unavailable type={type(dataset).__name__}",
        )
        return

    parts = [dataset_summary(dataset)]
    if identity is not None:
        parts.append(f"identity={identity}")

    coordinates = []
    for name in coordinate_names:
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
    parts.append(f"selected_vars={';'.join(coordinates) or 'none'}")
    parts.append(f"attrs={_selected_mapping(dataset.attrs, attribute_names)}")
    if presence_attributes:
        presence = ",".join(
            f"{name}={'set' if dataset.attrs.get(name) else 'missing'}"
            for name in presence_attributes
        )
        parts.append(f"attribute_presence={presence}")
    memory_checkpoint(label, " ".join(parts))


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
    for dim, chunks in zip(variable.dims, variable.chunks, strict=True):
        if not chunks:
            dimensions.append(f"{dim}:empty")
            continue
        minimum = min(chunks)
        maximum = max(chunks)
        size = str(minimum) if minimum == maximum else f"{minimum}-{maximum}"
        dimensions.append(f"{dim}:{len(chunks)}x{size}")
    return f"chunks={';'.join(dimensions)}"


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
