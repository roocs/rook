"""Result values produced by request decisions and execution."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RequestResult:
    """Result values produced by resolving and executing a request."""

    decision: object
    output_uris: list[str]

    @property
    def project(self):
        """Return the project resolved for the request."""
        return self.decision.project

    @property
    def use_original_files(self):
        """Return whether processing was skipped."""
        return self.decision.returns_original_files

    @property
    def original_file_urls(self):
        """Return original files selected by the request decision."""
        return self.decision.original_file_urls

    @property
    def search_result(self):
        """Return the catalog search result, when catalog lookup was used."""
        return self.decision.search_result

    @property
    def dataset_sources(self):
        """Return the dataset sources prepared for operation execution."""
        return self.decision.dataset_sources
