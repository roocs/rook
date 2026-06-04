from rook.utils.ops.concat import concat

from .input_utils import fix_parameters


def run_concat(args):
    args = fix_parameters(args)

    result = concat(**args)
    return result.file_uris
