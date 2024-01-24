import xarray as xr


def apply_atlas_fixes(ds):
    """
    See also clisops.ops.base_operaton._remove_redundant_fill_values
    """
    if isinstance(ds, xr.Dataset):
        var_list = list(ds.coords) + list(ds.data_vars)
    elif isinstance(ds, xr.DataArray):
        var_list = list(ds.coords)
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
    return ds
