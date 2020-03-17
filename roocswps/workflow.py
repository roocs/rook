import yaml
from copy import deepcopy
import networkx as nx

from .exceptions import WorkflowValidationError
from .operator import Subset, Average, Diff

import logging
LOGGER = logging.getLogger()


def load_wfdoc(path):
    wfdoc = yaml.load(open(path, "rb"))
    return wfdoc


def replace_inputs(wfdoc):
    steps = {}
    for step_id, step in wfdoc['steps'].items():
        steps[step_id] = deepcopy(step)
        # replace inputs
        for arg_id, arg in step['in'].items():
            if arg.startswith('inputs/'):
                input_id = arg.split('/')[1]
                steps[step_id]['in'][arg_id] = wfdoc['inputs'][input_id]
    LOGGER.debug(f'steps: {steps}')
    return steps


def build_tree(wfdoc):
    tree = nx.DiGraph()
    for output_id, output in wfdoc['outputs'].items():
        step_id = output.split('/')[0]
        tree.add_edge('root', output_id, arg_id=None)
        tree.add_edge(output_id, step_id, arg_id=None)
    for step_id, step in wfdoc['steps'].items():
        for arg_id, arg in step['in'].items():
            if arg.endswith('/output'):
                prev_step_id = arg.split('/')[0]
                tree.add_edge(step_id, prev_step_id, arg_id=arg_id)
    LOGGER.debug(f'tree: {tree.edges}')
    return tree


class Workflow(object):
    def __init__(self, data_root_dir, output_dir):
        self.subset_op = Subset(data_root_dir, output_dir)
        self.average_op = Average(data_root_dir, output_dir)
        self.diff_op = Diff(data_root_dir, output_dir)

    def validate(self, wfdoc):
        raise NotImplementedError("implemented in subclass")

    def run(self, path):
        wfdoc = load_wfdoc(path)
        self.validate(wfdoc)
        return self._run(wfdoc)

    def _run(self, wfdoc):
        raise NotImplementedError("implemented in subclass")


class SimpleWorkflow(Workflow):
    def validate(self, wfdoc):
        if 'doc' not in wfdoc:
            raise WorkflowValidationError('doc missing')
        if 'inputs' not in wfdoc:
            raise WorkflowValidationError('inputs missing')
        if 'steps' not in wfdoc:
            raise WorkflowValidationError('steps missing')
        return True

    def _run(self, wfdoc):
        data_ref = wfdoc['inputs']['data_ref']
        for step in wfdoc['steps']:
            data_ref = self._run_step(step, data_ref)
        return data_ref

    def _run_step(self, step, input):
        LOGGER.debug(f'run {step}')
        if 'subset' in step:
            step['subset']['data_ref'] = input
            result = self.subset_op.call(step['subset'])
        elif 'average' in step:
            step['average']['data_ref'] = input
            result = self.average_op.call(step['average'])
        else:
            result = None
        return result


class TreeWorkflow(Workflow):
    def validate(self, wfdoc):
        if 'doc' not in wfdoc:
            raise WorkflowValidationError('doc missing')
        if 'inputs' not in wfdoc:
            raise WorkflowValidationError('inputs missing')
        if 'outputs' not in wfdoc:
            raise WorkflowValidationError('outputs missing')
        if 'steps' not in wfdoc:
            raise WorkflowValidationError('steps missing')
        return True

    def _run(self, wfdoc):
        steps = replace_inputs(wfdoc)
        tree = build_tree(wfdoc)
        return self._run_tree(steps, tree, 'root')

    def _run_tree(self, steps, tree, step_id):
        tree_outputs = {}
        for next_step_id in tree.neighbors(step_id):
            data = tree.get_edge_data(step_id, next_step_id)
            LOGGER.debug(f'data={data}')
            tree_outputs[data['arg_id']] = self._run_tree(steps, tree, next_step_id)
        outputs = None
        LOGGER.debug(f'tree outputs={tree_outputs}')
        if step_id in steps:
            outputs = self._run_step(steps[step_id], tree_outputs)
        elif tree_outputs:
            outputs = list(tree_outputs.values())[0]
        LOGGER.debug(f'outputs={outputs}')
        return outputs

    def _run_step(self, step, inputs=None):
        LOGGER.debug(f'run step={step}, inputs={inputs}')
        if inputs:
            step['in'].update(inputs)
        if 'subset' == step['run']:
            result = self.subset_op.call(step['in'])
        elif 'average' == step['run']:
            result = self.average_op.call(step['in'])
        elif 'diff' == step['run']:
            result = self.diff_op.call(step['in'])
        else:
            result = None
        LOGGER.debug(f'run result={result}')
        return result
