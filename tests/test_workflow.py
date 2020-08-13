import tempfile

from rook import workflow

from .common import resource_file, CMIP5_ARCHIVE_ROOT


SIMPLE_WF = resource_file("subset_simple_wf.json")
TREE_WF = resource_file("subset_wf_1.json")
TREE_WF_2 = resource_file("subset_wf_2.json")
TREE_WF_3 = resource_file("subset_wf_3.json")


def test_validate_simple_wf():
    wfdoc = workflow.load_wfdoc(SIMPLE_WF)
    wf = workflow.SimpleWorkflow(
        base_dir=CMIP5_ARCHIVE_ROOT,
        output_dir=tempfile.mkdtemp())
    assert wf.validate(wfdoc) is True


def test_run_simple_wf():
    wfdoc = workflow.load_wfdoc(SIMPLE_WF)
    wf = workflow.SimpleWorkflow(
        base_dir=CMIP5_ARCHIVE_ROOT,
        output_dir=tempfile.mkdtemp())
    output = wf.run(wfdoc)
    assert 'output.nc' in output[0]


def test_validate_tree_wf():
    wfdoc = workflow.load_wfdoc(TREE_WF)
    wf = workflow.TreeWorkflow(
        base_dir=CMIP5_ARCHIVE_ROOT,
        output_dir=tempfile.mkdtemp())
    assert wf.validate(wfdoc) is True


def test_replace_inputs():
    wfdoc = workflow.load_wfdoc(TREE_WF)
    steps = workflow.replace_inputs(wfdoc)
    assert steps['subset_tas']['in']['data_ref'] == \
        ["cmip5.output1.MOHC.HadGEM2-ES.rcp85.mon.atmos.Amon.r1i1p1.latest.tas"]


def test_build_tree():
    wfdoc = workflow.load_wfdoc(TREE_WF)
    tree = workflow.build_tree(wfdoc)
    assert list(tree.edges) == [('root', 'output'), ('output', 'average_tas'), ('average_tas', 'subset_tas')]


def test_run_tree_wf():
    wfdoc = workflow.load_wfdoc(TREE_WF)
    wf = workflow.TreeWorkflow(
        base_dir=CMIP5_ARCHIVE_ROOT,
        output_dir=tempfile.mkdtemp())
    output = wf.run(wfdoc)
    assert 'output.nc' in output[0]


def test_run_tree_wf_2():
    wfdoc = workflow.load_wfdoc(TREE_WF)
    wf = workflow.TreeWorkflow(
        base_dir=CMIP5_ARCHIVE_ROOT,
        output_dir=tempfile.mkdtemp())
    output = wf.run(wfdoc)
    assert 'output.nc' in output[0]


def test_run_tree_wf_3():
    wfdoc = workflow.load_wfdoc(TREE_WF)
    wf = workflow.TreeWorkflow(
        base_dir=CMIP5_ARCHIVE_ROOT,
        output_dir=tempfile.mkdtemp())
    output = wf.run(wfdoc)
    assert 'output.nc' in output[0]


def test_workflow_runner_tree():
    wf = workflow.WorkflowRunner(
        base_dir=CMIP5_ARCHIVE_ROOT,
        output_dir=tempfile.mkdtemp())
    output = wf.run(TREE_WF)
    assert 'output.nc' in output[0]


def test_workflow_runner_simple():
    wf = workflow.WorkflowRunner(
        base_dir=CMIP5_ARCHIVE_ROOT,
        output_dir=tempfile.mkdtemp())
    output = wf.run(SIMPLE_WF)
    assert 'output.nc' in output[0]
