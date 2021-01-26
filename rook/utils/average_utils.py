from copy import deepcopy


def run_average(args):
    # Convert file list to directory if required
    original_collection = args.get("collection")
    # TODO: handle lazy load of daops
    # from daops.ops.average import average

    # result = average(args)
    # return result.file_uris
    # just to get orchestrate to work as average not implemented yet
    return original_collection.file_paths
