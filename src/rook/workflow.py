import logging
from copy import deepcopy
from pathlib import Path

import networkx as nx
import yaml

from .exceptions import WorkflowValidationError
from .operator import (
    AverageByDimension,
    AverageByTime,
    Concat,
    Regrid,
    Subset,
    WeightedAverage,
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
        wfdoc = yaml.load(Path(data).open("rb"), Loader=yaml.SafeLoader)
    else:
        wfdoc = yaml.load(data, Loader=yaml.SafeLoader)
    return wfdoc


def replace_inputs(wfdoc):
    steps = {}
    start_steps = []
    for step_id, step in wfdoc["steps"].items():
        steps[step_id] = deepcopy(step)
        # replace inputs
        for arg_id, arg in step["in"].items():
            if isinstance(arg, str) and arg.startswith("inputs/"):
                input_id = arg.split("/")[1]
                steps[step_id]["in"][arg_id] = wfdoc["inputs"][input_id]
                start_steps.append(step_id)
    for step_id in steps.keys():
        # fixes are only applied to start steps
        if step_id in start_steps:
            steps[step_id]["in"]["apply_fixes"] = steps[step_id]["in"].get(
                "apply_fixes", False
            )
        else:
            steps[step_id]["in"]["apply_fixes"] = False
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
        self.concat_op = Concat(output_dir)
        self.subset_op = Subset(output_dir)
        self.average_time_op = AverageByTime(output_dir)
        self.average_dim_op = AverageByDimension(output_dir)
        self.weighted_average_op = WeightedAverage(output_dir)
        self.regrid_op = Regrid(output_dir)
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
        if inputs:
            step["in"].update(inputs)
        if "subset" == step["run"]:
            collection = step["in"]["collection"]
            result = self.subset_op.call(step["in"])
            self.prov.add_operator(step_id, step["in"], collection, result)
        elif "average_time" == step["run"]:
            collection = step["in"]["collection"]
            result = self.average_time_op.call(step["in"])
            self.prov.add_operator(step_id, step["in"], collection, result)
        elif "average" == step["run"]:
            collection = step["in"]["collection"]
            result = self.average_dim_op.call(step["in"])
            self.prov.add_operator(step_id, step["in"], collection, result)
        elif "weighted_average" == step["run"]:
            collection = step["in"]["collection"]
            result = self.weighted_average_op.call(step["in"])
            self.prov.add_operator(step_id, step["in"], collection, result)
        elif "regrid" == step["run"]:
            collection = step["in"]["collection"]
            result = self.regrid_op.call(step["in"])
            self.prov.add_operator(step_id, step["in"], collection, result)
        elif "concat" == step["run"]:
            collection = step["in"]["collection"]
            result = self.concat_op.call(step["in"])
            self.prov.add_operator(step_id, step["in"], collection, result)
        else:
            result = None
        LOGGER.debug(f"run result={result}")
        return result
