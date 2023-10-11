def run_average_by_time(args):
    # TODO: handle lazy load of daops
    from daops.ops.average import average_time

    result = average_time(**args)
    return result.file_uris


def run_average_by_dim(args):
    from daops.ops.average import average_over_dims

    result = average_over_dims(**args)
    return result.file_uris


def run_average_by_shape(args):
    from daops.ops.average import average_shape

    result = average_shape(**args)
    return result.file_uris


def run_weighted_average(args):
    from daops.ops.average import average_over_dims

    args["apply_fixes"] = False
    args["dims"] = ["latitude", "longitude"]

    result = average_over_dims(**args)
    return result.file_uris
