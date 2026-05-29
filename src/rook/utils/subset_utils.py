from rook.utils.ops.subset import subset

from .input_utils import fix_parameters


def run_subset(args):
    args = fix_parameters(args)

    result = subset(**args)
    return result.file_uris
