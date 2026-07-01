"""Dispatch processing operations in serial or parallel mode."""

from loguru import logger


def dispatch(operation, dset, **kwargs):
    """Dispatch the operation to the selected execution mode."""
    logger.info("NOW SENDING TO PARALLEL DISPATCH MODE...")
    return process(operation, dset, mode="serial", **kwargs)


def process(operation, dset, mode="serial", **kwargs):
    """Run processing operation on a dataset."""
    op_name = operation.__name__

    if mode == "serial":
        logger.info(f"Running {op_name} [{mode}]: on Dataset with args: {kwargs}")
        result = operation(dset, **kwargs)
    else:
        result = dispatch(operation, dset, **kwargs)

    return result
