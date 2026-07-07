import logging
from copy import deepcopy
from pathlib import Path

import networkx as nx
import yaml

from .exceptions import WorkflowValidationError
from .operations import (
    WORKFLOW_OPERATIONS,
    make_workflow_operator,
)
from .provenance import Provenance

LOGGER = logging.getLogger()


def is_file(data):
    try:
        ok = Path(data).is_file()
    except OSError as e:
        LOGGER.warning(f"is_file check failed. reason={e}")
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

    def _run_tree(self, steps, tree, step_id):
        tree_outputs = {}
        for next_step_id in tree.neighbors(step_id):
            data = tree.get_edge_data(step_id, next_step_id)
            LOGGER.debug(f"data={data}")
            tree_outputs[data["arg_id"]] = self._run_tree(steps, tree, next_step_id)
        outputs = None
        LOGGER.debug(f"tree outputs={tree_outputs}")
        if step_id in steps:
            outputs = self._run_step(step_id, steps[step_id], tree_outputs)
        elif tree_outputs:
            outputs = next(iter(tree_outputs.values()))
            # outputs = list(tree_outputs.values())[0]
        LOGGER.debug(f"outputs={outputs}")
        return outputs

    def _run_step(self, step_id, step, inputs=None):
        LOGGER.debug(f"run step={step}, inputs={inputs}")
        operation_inputs = deepcopy(step["in"])
        if inputs:
            operation_inputs.update(inputs)

        operation = self.operations.get(step["run"])
        if operation is None:
            result = None
        else:
            collection = operation_inputs["collection"]
            result = operation.call(operation_inputs)
            self.prov.add_operator(step_id, operation_inputs, collection, result)

        LOGGER.debug(f"run result={result}")
        return result
