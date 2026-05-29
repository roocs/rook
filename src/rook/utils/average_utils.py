def run_average_by_time(args):
    from .ops_compat import run_daops_average_time

    return run_daops_average_time(args)


def run_average_by_dim(args):
    from .ops_compat import run_daops_average_over_dims

    return run_daops_average_over_dims(args)


def run_average_by_shape(args):
    from .ops_compat import run_daops_average_shape

    return run_daops_average_shape(args)
