"""Execution adapters used by WPS processes and workflows."""

import pathlib
import tempfile
from copy import deepcopy
from dataclasses import dataclass

from clisops.utils.file_utils import FileMapper, is_file_list

from rook.pflow import execute_resolved_request
from rook.pflow.sources import WorkflowFiles
from rook.utils.input_utils import (
    clean_inputs,
    fix_parameters,
    parse_custom_grid,
    resolve_to_file_paths,
)
from rook.operations.average import average_over_dims, average_shape, average_time
from rook.operations.concat import concat
from rook.operations.regrid import regrid
from rook.operations.subset import subset
from rook.utils.weighted_average_utils import run_weighted_average


@dataclass(frozen=True)
class WorkflowOperation:
    """Configuration for a workflow operation adapter."""

    prefix: str
    runner: object


def collect_file_uris(operation, args):
    """Run an operation function and return its file URIs."""
    return operation(**args).file_uris


def run_subset(args):
    args = fix_parameters(args)

    return collect_file_uris(subset, args)


def run_average_by_time(args):
    return collect_file_uris(average_time, args)


def run_average_by_dim(args):
    return collect_file_uris(average_over_dims, args)


def run_average_by_shape(args):
    return collect_file_uris(average_shape, args)


def run_concat(args):
    args = fix_parameters(args)

    return collect_file_uris(concat, args)


def run_regrid(args):
    if args.get("grid") == "custom" and "custom_grid" in args:
        args["grid"] = parse_custom_grid(args.pop("custom_grid"))

    return collect_file_uris(regrid, args)


def prepare_workflow_file_inputs(args, source):
    """Return operation inputs for files produced by a previous workflow step."""
    kwargs = deepcopy(args)
    clean_inputs(kwargs)
    file_paths = resolve_to_file_paths(source.files)
    kwargs["collection"] = FileMapper(file_paths)
    return kwargs


def run_workflow_files(args, runner):
    """Run an operation using previous workflow step output files."""
    source = WorkflowFiles(files=args["collection"])
    return runner(prepare_workflow_file_inputs(args, source))


class Operator:
    """Workflow operation adapter."""

    def __init__(self, output_dir, prefix, runner):
        if isinstance(output_dir, pathlib.Path):
            output_dir_ = output_dir.as_posix()
        else:
            output_dir_ = output_dir
        self.prefix = prefix
        self.runner = runner
        self.config = {
            "output_dir": output_dir_,
            # 'original_files': original_files
            # 'chunk_rules': dconfig.chunk_rules,
            # 'filenamer': dconfig.filenamer,
        }

    def call(self, args):
        # args.update(self.config)
        args["output_dir"] = self._get_output_dir()
        collection = args["collection"]  # collection is a list

        if is_file_list(collection):
            output_uris = run_workflow_files(args, self.runner)
        else:
            request_result = execute_resolved_request(collection, args, self.runner)
            output_uris = request_result.output_uris

        return output_uris

    def _get_output_dir(self):
        return tempfile.mkdtemp(dir=self.config["output_dir"], prefix=f"{self.prefix}_")


WORKFLOW_OPERATIONS = {
    "subset": WorkflowOperation(prefix="subset", runner=run_subset),
    "average_time": WorkflowOperation(prefix="average_time", runner=run_average_by_time),
    "average": WorkflowOperation(prefix="average", runner=run_average_by_dim),
    "average_shape": WorkflowOperation(prefix="average_shape", runner=run_average_by_shape),
    "weighted_average": WorkflowOperation(prefix="weighted_average", runner=run_weighted_average),
    "regrid": WorkflowOperation(prefix="regrid", runner=run_regrid),
    "concat": WorkflowOperation(prefix="concat", runner=run_concat),
}


def make_workflow_operator(name, output_dir):
    """Return the configured workflow operation adapter."""
    operation = WORKFLOW_OPERATIONS[name]
    return Operator(output_dir, prefix=operation.prefix, runner=operation.runner)


def subset_operator(output_dir):
    return make_workflow_operator("subset", output_dir)


def average_time_operator(output_dir):
    return make_workflow_operator("average_time", output_dir)


def average_dimension_operator(output_dir):
    return make_workflow_operator("average", output_dir)


def average_shape_operator(output_dir):
    return make_workflow_operator("average_shape", output_dir)


def weighted_average_operator(output_dir):
    return make_workflow_operator("weighted_average", output_dir)


def regrid_operator(output_dir):
    return make_workflow_operator("regrid", output_dir)


def concat_operator(output_dir):
    return make_workflow_operator("concat", output_dir)


Subset = subset_operator
AverageByTime = average_time_operator
AverageByDimension = average_dimension_operator
AverageByShape = average_shape_operator
WeightedAverage = weighted_average_operator
Regrid = regrid_operator
Concat = concat_operator
