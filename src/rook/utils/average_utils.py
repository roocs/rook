def run_average_by_time(args):
    from .ops.compat import run_average_time

    return run_average_time(args)


def run_average_by_dim(args):
    from .ops.compat import run_average_over_dims

    return run_average_over_dims(args)


def run_average_by_shape(args):
    from .ops.compat import run_average_shape

    return run_average_shape(args)
