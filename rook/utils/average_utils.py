def run_average_by_time(args):
    # TODO: handle lazy load of daops
    from daops.ops.average import average_time

    result = average_time(**args)
    return result.file_uris
