"""Process-memory checkpoints suitable for Slurm and PyWPS jobs."""

import os
from pathlib import Path
import sys

_STATUS_PATH = Path("/proc/self/status")


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
