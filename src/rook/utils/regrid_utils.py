from rook.utils.input_utils import parse_custom_grid


def run_regrid(args):
    from daops.ops.regrid import regrid

    args["apply_fixes"] = False

    # Handle custom grid parsing
    if args.get("grid") == "custom" and "custom_grid" in args:
        # parse the string into a tuple/list
        args["grid"] = parse_custom_grid(args.pop("custom_grid"))

    result = regrid(**args)

    return result.file_uris
