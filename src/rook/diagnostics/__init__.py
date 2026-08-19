"""Lightweight diagnostics for delegated Rook processing jobs."""

from .memory import (
    current_rss,
    malloc_trim,
    malloc_trim_diagnostic_enabled,
    memory_checkpoint,
)
from .xarray import dataset_signature, dataset_summary

__all__ = [
    "current_rss",
    "dataset_signature",
    "dataset_summary",
    "malloc_trim",
    "malloc_trim_diagnostic_enabled",
    "memory_checkpoint",
]
