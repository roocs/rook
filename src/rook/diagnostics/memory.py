"""Process-memory checkpoints suitable for Slurm and PyWPS jobs."""

import ctypes
import os
from pathlib import Path
import sys

_STATUS_PATH = Path("/proc/self/status")
_MALLOC_TRIM_ENV = "ROOK_DIAGNOSTIC_MALLOC_TRIM"


def current_rss():
    """Return the current process RSS reported by Linux procfs."""
    try:
        for line in _STATUS_PATH.read_text().splitlines():
            if line.startswith("VmRSS:"):
                return " ".join(line.split())
    except OSError:
        pass
    return "VmRSS: unavailable"


def memory_checkpoint(label, details=None):
    """Write one immediately flushed RSS diagnostic directly to stderr."""
    message = f"[rook-diagnostic] pid={os.getpid()} {current_rss()} {label}"
    if details:
        message = f"{message} | {details}"
    print(message, file=sys.stderr, flush=True)


def malloc_trim_diagnostic_enabled():
    """Return whether the opt-in native allocator diagnostic is enabled."""
    return os.environ.get(_MALLOC_TRIM_ENV, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def malloc_trim():
    """Ask glibc to release free heap pages, returning None when unavailable."""
    if not sys.platform.startswith("linux"):
        return None
    try:
        trim = ctypes.CDLL(None).malloc_trim
        trim.argtypes = [ctypes.c_size_t]
        trim.restype = ctypes.c_int
        return bool(trim(0))
    except (AttributeError, OSError):
        return None
