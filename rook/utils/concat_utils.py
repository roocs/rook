def run_concat(args):
    result = concat(**args)
    return result.file_uris


def concat(
    collection,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
    apply_fixes=True,
):
    # dummy concat operator
    from daops.ops.average import average_over_dims

    args = dict(
        collection=collection,
        dim="time",
        output_dir=output_dir,
        output_type=output_type,
        split_method=split_method,
        file_namer=file_namer,
        apply_fixes=apply_fixes,
    )
    return average_over_dims(**args)
