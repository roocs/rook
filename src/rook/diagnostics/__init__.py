"""Lightweight diagnostics for delegated Rook processing jobs."""

from .memory import (
    current_rss,
    free_memory_diagnostic_enabled,
    malloc_trim,
    malloc_trim_diagnostic_enabled,
    memory_checkpoint,
)
from .xarray import dataset_signature, dataset_summary

__all__ = [
    "current_rss",
    "dataset_signature",
    "dataset_summary",
    "free_memory_diagnostic_enabled",
    "malloc_trim",
    "malloc_trim_diagnostic_enabled",
    "memory_checkpoint",
]
