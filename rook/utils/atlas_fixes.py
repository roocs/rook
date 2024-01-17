def apply_atlas_fixes(ds_id, ds):
    ds.sst.encoding["_FillValue"] = None
    for cvar in ["member_id", "gcm_variant", "gcm_model", "gcm_institution"]:
        for en in ["zlib", "shuffle", "complevel"]:
            del ds[cvar].encoding[en]
    return ds
