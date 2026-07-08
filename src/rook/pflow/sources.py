"""Request source values."""

from dataclasses import dataclass

from .base import RequestSource


@dataclass(frozen=True)
class CatalogCollection(RequestSource):
    """A request source that should be resolved through a project catalog."""

    collection: list[str]
    project: str


@dataclass(frozen=True)
class DirectDataset(RequestSource):
    """A request source that should be processed directly without catalog lookup."""

    collection: list[str]
    project: str


@dataclass(frozen=True)
class WorkflowFiles(RequestSource):
    """Files produced by an earlier workflow step."""

    files: list[str]
