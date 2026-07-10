"""Module for editing dataset and variable attributes."""

from rook.fixes.legacy.utils.common_utils import handle_derive_str


def edit_var_attrs(ds_id, ds, **operands):
    """Edit variable attrs and return the dataset."""
    var_id = operands.get("var_id")

    for k, v in operands.get("attrs").items():
        v = handle_derive_str(v, ds_id, ds)
        ds[var_id].attrs[k] = v

    return ds


def edit_global_attrs(ds_id, ds, **operands):
    """Edit global attrs and return the dataset."""
    for k, v in operands.get("attrs").items():
        v = handle_derive_str(v, ds_id, ds)
        ds.attrs[k] = v

    return ds


def add_global_attrs_if_needed(ds_id, ds, **operands):
    """Add missing global attrs and return the dataset."""
    for k, v in operands.get("attrs").items():
        v = handle_derive_str(v, ds_id, ds)
        if not ds.attrs.get(k, None):
            ds.attrs[k] = v

    return ds


def remove_coord_attr(ds_id, ds, **operands):
    """Remove coordinates encoding attributes from selected variables."""
    var_ids = handle_derive_str(operands.get("var_ids"), ds_id, ds)

    for v in var_ids:
        ds[v].encoding["coordinates"] = None

    return ds
