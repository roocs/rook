from .atlas_fixes import apply_atlas_fixes

from clisops.project_utils import derive_ds_id


def apply_fixes(dset, ds):
    try:
        ds_id = derive_ds_id(dset)
    except Exception:
        ds_id = ""

    if ds_id.startswith("c3s-ipcc-atlas") or ds_id.startswith("c3s-cica-atlas"):
        ds_mod = apply_atlas_fixes(ds_id, ds)
    else:
        ds_mod = ds
    return ds_mod
