from .input_utils import fix_parameters


def run_subset(args):
    # TODO: handle lazy load of daops
    from daops.ops.subset import subset

    args = fix_parameters(args)

    result = subset(**args)
    return result.file_uris
