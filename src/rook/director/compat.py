"""Compatibility helpers for director runtime dependencies."""

import collections
import os

try:
    from daops.utils import is_characterised as _daops_is_characterised
except Exception:  # pragma: no cover
    _daops_is_characterised = None

class ResultSet:
    """A class to hold operation results with file URI extraction."""

    def __init__(self, inputs=None):  # noqa: D107
        self._results = collections.OrderedDict()
        self.metadata = {"inputs": inputs, "process": "something", "version": 0.1}
        self.file_uris = []

    def add(self, dset, result):
        """Add outputs for a dataset and collect file-like URIs."""
        self._results[dset] = result

        for item in result:
            if isinstance(item, str) and (
                os.path.isfile(item) or item.startswith("https")
            ):
                self.file_uris.append(item)


def is_characterised(*args, **kwargs):
    """Proxy to daops characterisation lookup, with safe fallback."""
    if _daops_is_characterised is None:
        # Conservative fallback: treat as not characterised when daops is absent.
        return False
    return _daops_is_characterised(*args, **kwargs)
