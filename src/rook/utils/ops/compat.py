"""Compatibility wrappers around operation backends."""

def run_average_time(args):
    from rook.utils.ops.average import average_time

    return average_time(**args).file_uris


def run_average_over_dims(args):
    from rook.utils.ops.average import average_over_dims

    return average_over_dims(**args).file_uris


def run_average_shape(args):
    from rook.utils.ops.average import average_shape

    return average_shape(**args).file_uris


def run_regrid(args):
    from rook.utils.ops.regrid import regrid

    return regrid(**args).file_uris


def run_custom_average(args, operation_callable):
    from rook.utils.ops.average import Average

    class _Average(Average):
        def get_operation_callable(self):
            return operation_callable

    return _Average(**args).calculate().file_uris
