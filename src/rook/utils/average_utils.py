def run_average_by_time(args):
    from .ops.average import average_time

    return average_time(**args).file_uris


def run_average_by_dim(args):
    from .ops.average import average_over_dims

    return average_over_dims(**args).file_uris


def run_average_by_shape(args):
    from .ops.average import average_shape

    return average_shape(**args).file_uris
