"""Process-memory checkpoints suitable for Slurm and PyWPS jobs."""

import ctypes
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from rook import config


_STATUS_PATH = Path("/proc/self/status")


def current_timestamp():
    """Return the current UTC time in a compact ISO-8601 form."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


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
    message = (
        f"[diagnostic] {current_timestamp()} pid={os.getpid()} "
        f"{current_rss()} {label}"
    )
    if details:
        message = f"{message} | {details}"
    print(message, file=sys.stderr, flush=True)


def free_memory_diagnostic_enabled():
    """Return whether explicit Python and native memory cleanup is enabled."""
    return config.get_diagnostic_free_memory()


def malloc_trim_diagnostic_enabled():
    """Return whether native allocator cleanup is enabled."""
    return free_memory_diagnostic_enabled()


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
