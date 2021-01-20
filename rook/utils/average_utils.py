from copy import deepcopy

from .input_utils import resolve_collection_if_files


def run_average(args):
    # Convert file list to directory if required
    kwargs = deepcopy(args)
    kwargs["collection"] = resolve_collection_if_files(args.get("collection"))

    # TODO: handle lazy load of daops
    from daops.ops.average import average_over_dims

    result = average_over_dims(**kwargs)
    return result.file_uris
