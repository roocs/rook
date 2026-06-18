"""Helper utilities for operation plumbing."""

import collections


def wrap_sequence(obj):
    """Return a list for scalar inputs and preserve sequences."""
    if isinstance(obj, str):
        obj = [obj]
    return obj


def ordered_dict():
    """Return an OrderedDict instance."""
    return collections.OrderedDict()
