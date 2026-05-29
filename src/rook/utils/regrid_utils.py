from rook.utils.input_utils import parse_custom_grid
from rook.utils.ops.regrid import regrid as ops_regrid


def run_regrid(args):
    args["apply_fixes"] = False

    # Handle custom grid parsing
    if args.get("grid") == "custom" and "custom_grid" in args:
        # parse the string into a tuple/list
        args["grid"] = parse_custom_grid(args.pop("custom_grid"))

    return ops_regrid(**args).file_uris
