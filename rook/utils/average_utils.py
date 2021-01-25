from copy import deepcopy

from .input_utils import resolve_collection_if_files


def run_average(kwargs):
    # Convert file list to directory if required
    original_collection = kwargs.get("collection")
    # TODO: handle lazy load of daops
    # from daops.ops.average import average

    # result = average(**kwargs)
    # return result.file_uris
    return original_collection
