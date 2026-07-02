"""Execute request plans and adapt their outputs."""

import pathlib
from collections import OrderedDict
from dataclasses import dataclass

from pywps.app.exceptions import ProcessError

from rook.utils.input_utils import clean_inputs

from .planning import plan_request


@dataclass(frozen=True)
class RequestResult:
    """Result values produced by planning and executing a request."""

    plan: object
    output_uris: list[str]

    @property
    def project(self):
        """Return the project resolved for the request."""
        return self.plan.project

    @property
    def use_original_files(self):
        """Return whether processing was skipped."""
        return self.plan.returns_original_files

    @property
    def original_file_urls(self):
        """Return original files selected by the request plan."""
        return self.plan.original_file_urls

    @property
    def search_result(self):
        """Return the catalog search result, when catalog lookup was used."""
        return self.plan.search_result

    @property
    def dataset_sources(self):
        """Return the dataset sources prepared for operation execution."""
        return self.plan.dataset_sources


class OriginalFileResult:
    """Collect original-file outputs as file URI values."""

    def __init__(self):
        self._results = OrderedDict()
        self.file_uris = []

    def add(self, dataset_id, file_urls):
        """Add original URLs for a dataset."""
        self._results[dataset_id] = file_urls

        for item in file_urls:
            if isinstance(item, str) and (
                pathlib.Path(item).is_file() or item.startswith("https")
            ):
                self.file_uris.append(item)


def execute_request(collection, inputs, runner):
    """Plan and execute a request."""
    plan = plan_request(collection, inputs)
    output_uris = execute_plan(plan, inputs, runner)
    return RequestResult(plan=plan, output_uris=output_uris)


def execute_plan(plan, inputs, runner):
    """Return output URIs for a planned request."""
    if plan.returns_original_files:
        return collect_original_file_uris(plan.original_file_urls)

    return run_operation(plan, inputs, runner)


def collect_original_file_uris(original_file_urls):
    """Return original file URIs in the same shape as operation outputs."""
    result = OriginalFileResult()

    for ds_id, file_urls in original_file_urls.items():
        result.add(ds_id, file_urls)

    return result.file_uris


def run_operation(plan, inputs, runner):
    """Run an operation with inputs prepared from a request plan."""
    operation_inputs = prepare_operation_inputs(plan, inputs)

    try:
        return runner(operation_inputs)
    except Exception as e:
        raise ProcessError(f"{e}")


def prepare_operation_inputs(plan, inputs):
    """Return cleaned operation inputs without mutating caller inputs."""
    operation_inputs = dict(inputs)
    clean_inputs(operation_inputs)

    if plan.dataset_sources:
        operation_inputs["collection"] = list(plan.dataset_sources)

    return operation_inputs
