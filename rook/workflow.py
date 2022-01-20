import logging
import os
from copy import deepcopy

import networkx as nx
import yaml

from .exceptions import WorkflowValidationError
from .operator import Average, Diff, Subset
from .provenance import Provenance

LOGGER = logging.getLogger()


def load_wfdoc(data):
    if os.path.isfile(data):
        wfdoc = yaml.load(open(data, "rb"), Loader=yaml.SafeLoader)
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
    for step_id, step in steps.items():
        # fixes are only applied to start steps
        if step_id in start_steps:
            steps[step_id]["in"]["apply_fixes"] = steps[step_id]["in"].get(
                "apply_fixes", True
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


class WorkflowRunner(object):
    def __init__(self, output_dir):
        self.workflow = TreeWorkflow(output_dir)

    def run(self, path):
        wfdoc = load_wfdoc(path)
        if "steps" not in wfdoc:
            raise WorkflowValidationError("steps missing")
        return self.workflow.run(wfdoc)

    @property
    def provenance(self):
        return self.workflow.prov


class BaseWorkflow(object):
    def __init__(self, output_dir):
        self.subset_op = Subset(output_dir)
        self.average_op = Average(output_dir)
        self.diff_op = Diff(output_dir)
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


class TreeWorkflow(BaseWorkflow):
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
            outputs = list(tree_outputs.values())[0]
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
        elif "average" == step["run"]:
            collection = step["in"]["collection"]
            result = self.average_op.call(step["in"])
            self.prov.add_operator(step_id, step["in"], collection, result)
        elif "diff" == step["run"]:
            result = self.diff_op.call(step["in"])
            self.prov.add_operator(step_id, step["in"], ["missing"], result)
        else:
            result = None
        LOGGER.debug(f"run result={result}")
        return result
