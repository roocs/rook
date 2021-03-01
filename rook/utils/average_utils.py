def run_average(args):
    # TODO: handle lazy load of daops
    from daops.ops.average import average_over_dims

    result = average_over_dims(**args)
    return result.file_uris
