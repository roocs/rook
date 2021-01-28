def run_subset(args):
    # TODO: handle lazy load of daops
    from daops.ops.subset import subset

    result = subset(**args)
    return result.file_uris
