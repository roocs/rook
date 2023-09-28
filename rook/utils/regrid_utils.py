def run_regrid(args):
    from daops.ops.average import average_over_dims

    args["apply_fixes"] = False
    args["dims"] = ["latitude", "longitude"]

    result = average_over_dims(**args)
    return result.file_uris
