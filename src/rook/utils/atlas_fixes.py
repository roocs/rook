from typing import Union

import xarray as xr


def apply_atlas_fixes(ds_id, ds):
    ds_mod = fix_deflation(ds)
    ds_mod = add_project_id(ds_id, ds)
    return ds_mod


def add_project_id(ds_id, ds):
    project_id = ds_id.split(".")[0]
    ds.attrs["project_id"] = project_id
    return ds


def fix_deflation(ds: Union[xr.Dataset, xr.DataArray]):
    """See also: clisops.ops.base_operation._remove_redundant_fill_values."""
    if isinstance(ds, xr.Dataset):
        var_list = list(ds.coords) + list(ds.data_vars)
    elif isinstance(ds, xr.DataArray):
        var_list = list(ds.coords)
    else:
        raise ValueError("Input must be an xarray Dataset or DataArray")
    # DEBUG
    for var in var_list:
        print("debug var", var, ds[var].encoding)
    # DEBUG END
    for var in var_list:
        ds[var].encoding["_FillValue"] = None
    # Remove string deflation options if applicable
    for cvar in [
        "member_id",
        "gcm_variant",
        "gcm_model",
        "gcm_institution",
        "rcm_variant",
        "rcm_model",
        "rcm_institution",
    ]:
        for en in ["zlib", "shuffle", "complevel"]:
            try:
                del ds[cvar].encoding[en]
            except KeyError:
                pass
    # use compression level 1
    for var in ds.data_vars:
        complevel = ds[var].encoding.get("complevel", 0)
        if complevel > 1:
            ds[var].encoding["complevel"] = 1
            ds[var].encoding["zlib"] = True
            ds[var].encoding["shuffle"] = True
    return ds
