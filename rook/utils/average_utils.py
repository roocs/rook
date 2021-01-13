from copy import deepcopy

from .input_utils import resolve_collection_if_files


def run_average(args):
    # Convert file list to directory if required
    kwargs = deepcopy(args)
    original_collection = args.get("collection")
    kwargs["collection"] = resolve_collection_if_files(original_collection)

    # TODO: handle lazy load of daops
    # from daops.ops.average import average

    # result = average(**kwargs)
    # return result.file_uris
    return original_collection
