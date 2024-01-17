from .atlas_fixes import apply_atlas_fixes


def apply_fixes(ds_id, ds):
    if ds_id.startswith("c3s-ipcc-atlas") or ds_id.startswith("c3s-cica-atlas"):
        ds_mod = apply_atlas_fixes(ds_id, ds)
    else:
        ds_mod = ds
    return ds_mod
