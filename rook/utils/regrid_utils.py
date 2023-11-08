def run_regrid(args):
    from daops.ops.average import average_over_dims

    args["apply_fixes"] = False
    args["dims"] = ["latitude", "longitude"]

    # remove regrid arguments
    args.pop("method", None)
    args.pop("grid", None)

    result = average_over_dims(**args)
    return result.file_uris
