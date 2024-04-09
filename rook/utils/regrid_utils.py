def run_regrid(args):
    from daops.ops.regrid import regrid

    args["apply_fixes"] = False

    result = regrid(**args)

    return result.file_uris
