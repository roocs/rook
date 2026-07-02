"""Dispatch processing operations in serial or parallel mode."""

from loguru import logger


def process(operation, dset, **kwargs):
    """Run processing operation on a dataset."""
    op_name = operation.__name__
    logger.info(f"Running {op_name}: on Dataset with args: {kwargs}")
    return operation(dset, **kwargs)
