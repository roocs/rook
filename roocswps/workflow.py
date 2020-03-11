import daops
import yaml
from copy import deepcopy
import networkx as nx

from .exceptions import WorkflowValidationError

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
        tree.add_edge('root', output_id)
        tree.add_edge(output_id, step_id)
    for step_id, step in wfdoc['steps'].items():
        for arg_id, arg in step['in'].items():
            if arg.endswith('/output'):
                prev_step_id = arg.split('/')[0]
                tree.add_edge(step_id, prev_step_id)
    LOGGER.debug(f'tree: {tree.edges}')
    return tree


class Workflow(object):
    def __init__(self, data_root_dir, output_dir):
        self.config = {
            'data_root_dir': data_root_dir,
            'output_dir': output_dir,
            # 'chunk_rules': dconfig.chunk_rules,
            # 'filenamer': dconfig.filenamer,
        }

    def validate(self, wfdoc):
        raise NotImplementedError("implemented in subclass")

    def run(self, path):
        wfdoc = load_wfdoc(path)
        self.validate(wfdoc)
        return self._run(wfdoc)

    def _run(self, wfdoc):
        raise NotImplementedError("implemented in subclass")

    def _run_subset(self, args, data_refs):
        kwargs = {}
        if 'time' in args:
            kwargs['time'] = args['time'].split('/')
        if 'space' in args:
            kwargs['space'] = [float(item) for item in args['space'].split(',')]
        kwargs.update(self.config)
        result = daops.subset(
            data_refs,
            **kwargs,
        )
        return result.file_paths

    def _run_average(self, args, data_refs):
        return data_refs


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
        data_refs = wfdoc['inputs']['data_ref']
        for step in wfdoc['steps']:
            data_refs = self._run_step(step, data_refs)
        return data_refs

    def _run_step(self, step, data_refs):
        LOGGER.debug(f'run {step}')
        if 'subset' in step:
            result = self._run_subset(step['subset'], data_refs)
        elif 'average' in step:
            result = self._run_average(step['average'], data_refs)
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
        data_refs = None
        if step_id in steps:
            if 'data_ref' in steps[step_id]['in']:
                data_refs = steps[step_id]['in']['data_ref']
        for next_step_id in tree.neighbors(step_id):
            data_refs = self._run_tree(steps, tree, next_step_id)
        if step_id in steps:
            data_refs = self._run_step(steps[step_id], data_refs)
        return data_refs

    def _run_step(self, step, data_refs):
        LOGGER.debug(f'run {step}')
        if 'subset' == step['run']:
            result = self._run_subset(step['in'], data_refs)
        elif 'average' == step['run']:
            result = self._run_average(step['in'], data_refs)
        else:
            result = None
        return result
