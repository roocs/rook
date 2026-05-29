"""Select which Operation base class to use for ops migration."""

import os

from daops.ops.base import Operation as DaopsOperation

from .base import Operation as LocalOperation


def _as_bool(value, default):
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_operation_base(default_local=True):
    """Return rook-local or daops Operation based on ROOK_USE_LOCAL_OPS_BASE.

    Set ROOK_USE_LOCAL_OPS_BASE=0 to force legacy daops base.
    """

    use_local = _as_bool(
        os.getenv("ROOK_USE_LOCAL_OPS_BASE"),
        default_local,
    )

    if use_local:
        return LocalOperation

    return DaopsOperation