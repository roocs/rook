import logging
from copy import deepcopy
from pathlib import Path
import sys

import networkx as nx
import yaml

from .exceptions import WorkflowValidationError
from .operations import (
    WORKFLOW_OPERATIONS,
    make_workflow_operator,
)
from .provenance import Provenance

LOGGER = logging.getLogger()
_PUSHDOWN_PARAMETERS = ("time", "time_components", "area")
_TEMPORAL_PUSHDOWN_PARAMETERS = _PUSHDOWN_PARAMETERS[:2]
_SUBSET_SELECTION_PARAMETERS = {"time", "time_components", "area", "level"}
_SUBSET_PASSTHROUGH_DEFAULTS = {
    "output_type": {None, "netcdf"},
    "split_method": {None, "time:auto"},
    "file_namer": {None, "standard"},
    "ignore_undetected_dims": {None, False},
}
_SUBSET_PASSTHROUGH_CONTROLS = {"original_files", "pre_checked"}


class _SubsetPushdown(dict):
    """Subset hints plus shared state about their physical execution."""

    def __init__(self, values=None, *, state=None):
        super().__init__(values or {})
        self._state = (
            state if state is not None else {"attempted": set(), "failed": set()}
        )

    def copy(self):
        return type(self)(self, state=self._state)

    def record(self, name, successful):
        self._state["attempted"].add(name)
        if not successful:
            self._state["failed"].add(name)

    def reject(self, names):
        for name in names:
            if name in self:
                self.record(name, False)

    def consumed(self, name):
        return name in self._state["attempted"] and name not in self._state["failed"]

    def consumed_selection(self):
        return any(self.consumed(name) for name in _PUSHDOWN_PARAMETERS)


def is_file(data):
    try:
        ok = Path(data).is_file()
    except OSError as e:
        LOGGER.debug(f"is_file check failed. reason={e}")
        ok = False
    return ok


def load_wfdoc(data):
    if is_file(data):
        with Path(data).open("rb") as fp:
            wfdoc = yaml.load(fp, Loader=yaml.SafeLoader)
    else:
        wfdoc = yaml.load(data, Loader=yaml.SafeLoader)
    return wfdoc


def replace_inputs(wfdoc):
    steps = {}
    for step_id, step in wfdoc["steps"].items():
        steps[step_id] = deepcopy(step)
        # replace inputs
        for arg_id, arg in step["in"].items():
            if isinstance(arg, str) and arg.startswith("inputs/"):
                input_id = arg.split("/")[1]
                steps[step_id]["in"][arg_id] = wfdoc["inputs"][input_id]
    LOGGER.debug(f"steps: {steps}")
    return steps


def build_tree(wfdoc):
    tree = nx.DiGraph()
    for output_id, output in wfdoc["outputs"].items():
        step_id = output.split("/")[0]
        tree.add_edge("root", output_id, arg_id=None)
        tree.add_edge(output_id, step_id, arg_id=None)
    for step_id, step in wfdoc["steps"].items():
        for arg_id, arg in step["in"].items():
            if isinstance(arg, str) and arg.endswith("/output"):
                prev_step_id = arg.split("/")[0]
                tree.add_edge(step_id, prev_step_id, arg_id=arg_id)
    LOGGER.debug(f"tree: {tree.edges}")
    return tree


class WorkflowRunner:
    def __init__(self, output_dir):
        self.workflow = Workflow(output_dir)

    def run(self, path):
        wfdoc = load_wfdoc(path)
        if "steps" not in wfdoc:
            raise WorkflowValidationError("steps missing")
        return self.workflow.run(wfdoc)

    @property
    def provenance(self):
        return self.workflow.prov


class BaseWorkflow:
    def __init__(self, output_dir):
        self.operations = {
            name: make_workflow_operator(name, output_dir)
            for name in WORKFLOW_OPERATIONS
        }
        self.prov = Provenance(output_dir)

    def validate(self, wfdoc):
        raise NotImplementedError("implemented in subclass")

    def run(self, wfdoc):
        self.validate(wfdoc)
        self.prov.start(workflow=True)
        outputs = self._run(wfdoc)
        self.prov.stop()
        return outputs

    def _run(self, wfdoc):
        raise NotImplementedError("implemented in subclass")


class Workflow(BaseWorkflow):
    def validate(self, wfdoc):
        if "doc" not in wfdoc:
            raise WorkflowValidationError("doc missing")
        if "inputs" not in wfdoc:
            raise WorkflowValidationError("inputs missing")
        if "outputs" not in wfdoc:
            raise WorkflowValidationError("outputs missing")
        if "steps" not in wfdoc:
            raise WorkflowValidationError("steps missing")
        return True

    def _run(self, wfdoc):
        steps = replace_inputs(wfdoc)
        tree = build_tree(wfdoc)
        return self._run_tree(steps, tree, "root")

    def _run_tree(self, steps, tree, step_id, subset_pushdown=None):
        step = steps.get(step_id)
        subset_pushdown = _subset_pushdown_for_upstream(step, subset_pushdown)
        tree_outputs = {}
        for next_step_id in tree.neighbors(step_id):
            data = tree.get_edge_data(step_id, next_step_id)
            LOGGER.debug(f"data={data}")
            tree_outputs[data["arg_id"]] = self._run_tree(
                steps,
                tree,
                next_step_id,
                subset_pushdown=subset_pushdown,
            )
        outputs = None
        LOGGER.debug(f"tree outputs={tree_outputs}")
        if step_id in steps:
            outputs = self._run_step(
                step_id,
                steps[step_id],
                tree_outputs,
                subset_pushdown=subset_pushdown,
            )
        elif tree_outputs:
            outputs = next(iter(tree_outputs.values()))
            # outputs = list(tree_outputs.values())[0]
        LOGGER.debug(f"outputs={outputs}")
        return outputs

    def _run_step(self, step_id, step, inputs=None, subset_pushdown=None):
        LOGGER.debug(f"run step={step}, inputs={inputs}")
        if subset_pushdown is not None and not isinstance(
            subset_pushdown, _SubsetPushdown
        ):
            subset_pushdown = _SubsetPushdown(subset_pushdown)
        operation_inputs = deepcopy(step["in"])
        if inputs:
            operation_inputs.update(inputs)
        pushdown_results = {}
        if step["run"] == "concat" and subset_pushdown:
            for name, value in subset_pushdown.items():
                existing = operation_inputs.get(name)
                successful = existing is None or existing == value
                if existing is None:
                    operation_inputs[name] = value
                if name in _PUSHDOWN_PARAMETERS:
                    pushdown_results[name] = successful
        if step["run"] == "subset" and isinstance(subset_pushdown, _SubsetPushdown):
            for name in _PUSHDOWN_PARAMETERS:
                if subset_pushdown.consumed(name):
                    operation_inputs.pop(name, None)

            can_pass = _subset_can_pass_through(operation_inputs, subset_pushdown)
            consumed = {
                name: subset_pushdown.consumed(name) for name in _PUSHDOWN_PARAMETERS
            }
            print(
                "[workflow] subset pass-through check "
                f"step={step_id} "
                f"inputs={operation_inputs!r} "
                f"pushdown={dict(subset_pushdown)!r} "
                f"attempted={subset_pushdown._state['attempted']!r} "
                f"failed={subset_pushdown._state['failed']!r} "
                f"consumed={consumed!r} "
                f"can_pass={can_pass}",
                file=sys.stderr,
                flush=True,
            )
            if can_pass:
                collection = operation_inputs["collection"]
                result = collection
                self.prov.add_operator(step_id, operation_inputs, collection, result)
                LOGGER.debug(f"pass through subset result={result}")
                return result

        operation = self.operations.get(step["run"])
        if operation is None:
            for name in pushdown_results:
                subset_pushdown.record(name, False)
            result = None
        else:
            collection = operation_inputs["collection"]
            result = operation.call(operation_inputs)
            for name, successful in pushdown_results.items():
                subset_pushdown.record(name, successful)
            self.prov.add_operator(step_id, operation_inputs, collection, result)

        LOGGER.debug(f"run result={result}")
        return result


def _subset_pushdown_for_upstream(step, inherited=None):
    """Carry safe downstream subset hints into an upstream concat."""
    if not isinstance(inherited, _SubsetPushdown):
        inherited = _SubsetPushdown(inherited)
    if step is None:
        return inherited

    operation = step["run"]
    if operation == "subset":
        return _SubsetPushdown(
            {
                name: step["in"][name]
                for name in ("time", "time_components", "area")
                if step["in"].get(name) is not None
            }
        )
    if operation == "concat":
        return inherited
    if operation == "average":
        dimensions = step["in"].get("dims") or ()
        if isinstance(dimensions, str):
            dimensions = (dimensions,)
        forwarded = inherited.copy()
        if "time" in dimensions:
            forwarded.reject(_TEMPORAL_PUSHDOWN_PARAMETERS)
            forwarded.pop("time", None)
            forwarded.pop("time_components", None)
        if set(dimensions).intersection(
            {"latitude", "longitude", "lat", "lon", "x", "y"}
        ):
            forwarded.reject(("area",))
            forwarded.pop("area", None)
        return forwarded
    if operation in {"regrid", "average_shape", "weighted_average"}:
        forwarded = inherited.copy()
        forwarded.reject(("area",))
        forwarded.pop("area", None)
        return forwarded
    inherited.reject(_PUSHDOWN_PARAMETERS)
    return _SubsetPushdown(state=getattr(inherited, "_state", None))


def _subset_can_pass_through(operation_inputs, subset_pushdown):
    """Return whether a physically empty optimized subset can be bypassed."""
    if not subset_pushdown.consumed_selection():
        return False

    for name, value in operation_inputs.items():
        if name == "collection" or value is None:
            continue
        if name in _SUBSET_SELECTION_PARAMETERS:
            return False
        if name in _SUBSET_PASSTHROUGH_DEFAULTS:
            if value not in _SUBSET_PASSTHROUGH_DEFAULTS[name]:
                return False
            continue
        if name in _SUBSET_PASSTHROUGH_CONTROLS:
            continue
        return False
    return True
