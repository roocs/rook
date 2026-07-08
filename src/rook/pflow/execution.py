"""Execute request decisions and adapt their outputs."""

import pathlib

from pywps.app.exceptions import ProcessError

from rook.utils.input_utils import clean_inputs

from .resolver import resolve_request_decision
from .results import RequestResult


def execute_request(collection, inputs, runner):
    """Resolve and execute a request."""
    decision = resolve_request_decision(collection, inputs)
    output_uris = execute_decision(decision, inputs, runner)
    return RequestResult(decision=decision, output_uris=output_uris)


def execute_decision(decision, inputs, runner):
    """Return output URIs for a request decision."""
    if decision.returns_original_files:
        return collect_original_file_uris(decision.original_file_urls)

    return run_operation(decision, inputs, runner)


def collect_original_file_uris(original_file_urls):
    """Return original file URIs in the same shape as operation outputs."""
    file_uris = []

    for file_urls in original_file_urls.values():
        file_uris.extend(item for item in file_urls if isinstance(item, str) and (pathlib.Path(item).is_file() or item.startswith("https")))

    return file_uris


def run_operation(decision, inputs, runner):
    """Run an operation with inputs prepared from a request decision."""
    operation_inputs = prepare_operation_inputs(decision, inputs)

    try:
        return runner(operation_inputs)
    except Exception as e:
        raise ProcessError(f"{e}")


def prepare_operation_inputs(decision, inputs):
    """Return cleaned operation inputs without mutating caller inputs."""
    operation_inputs = dict(inputs)
    clean_inputs(operation_inputs)

    if decision.dataset_sources:
        operation_inputs["collection"] = list(decision.dataset_sources)

    return operation_inputs
