"""Compatibility wrappers around operation backends."""

from rook.utils.ops.base import Operation as DaopsOperation
from rook.utils.ops import normalise as daops_normalise


def run_daops_average_time(args):
    from daops.ops.average import average_time

    return average_time(**args).file_uris


def run_daops_average_over_dims(args):
    from daops.ops.average import average_over_dims

    return average_over_dims(**args).file_uris


def run_daops_average_shape(args):
    from daops.ops.average import average_shape

    return average_shape(**args).file_uris


def run_daops_regrid(args):
    from daops.ops.regrid import regrid

    return regrid(**args).file_uris


def run_daops_custom_average(args, operation_callable):
    from daops.ops.average import Average as DaopsAverage

    class _Average(DaopsAverage):
        def get_operation_callable(self):
            return operation_callable

    return _Average(**args).calculate().file_uris
