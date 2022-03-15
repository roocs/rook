def run_average(args):
    # TODO: handle lazy load of daops
    from daops.ops.average import average_time

    result = average_time(**args)
    return result.file_uris
