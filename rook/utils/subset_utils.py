def run_subset(kwargs):

    # TODO: handle lazy load of daops
    from daops.ops.subset import subset

    result = subset(**kwargs)
    return result.file_uris
