import tempfile

from rook import workflow

from .common import resource_file


TREE_WF = resource_file("subset_wf_1.json")
TREE_WF_2 = resource_file("subset_wf_2.json")
TREE_WF_3 = resource_file("subset_wf_3.json")


def test_validate_tree_wf():
    wfdoc = workflow.load_wfdoc(TREE_WF)
    wf = workflow.TreeWorkflow(
        output_dir=tempfile.mkdtemp())
    assert wf.validate(wfdoc) is True


def test_replace_inputs():
    wfdoc = workflow.load_wfdoc(TREE_WF)
    steps = workflow.replace_inputs(wfdoc)
    assert steps['subset_tas']['in']['collection'] == \
        ["cmip5.output1.MOHC.HadGEM2-ES.rcp85.mon.atmos.Amon.r1i1p1.latest.tas"]


def test_build_tree():
    wfdoc = workflow.load_wfdoc(TREE_WF)
    tree = workflow.build_tree(wfdoc)
    assert list(tree.edges) == [('root', 'output'), ('output', 'average_tas'), ('average_tas', 'subset_tas')]


def test_run_tree_wf():
    wfdoc = workflow.load_wfdoc(TREE_WF)
    wf = workflow.TreeWorkflow(
        output_dir=tempfile.mkdtemp())
    output = wf.run(wfdoc)
    assert 'tas_mon_HadGEM2-ES_rcp85_r1i1p1_20850116-21201216.nc' in output[0]


def test_run_tree_wf_2():
    wfdoc = workflow.load_wfdoc(TREE_WF_2)
    wf = workflow.TreeWorkflow(
        output_dir=tempfile.mkdtemp())
    output = wf.run(wfdoc)
    assert 'tas_mon_HadGEM2-ES_rcp85_r1i1p1_20900116-21001216.nc' in output[0]


def test_run_tree_wf_3():
    wfdoc = workflow.load_wfdoc(TREE_WF_3)
    wf = workflow.TreeWorkflow(
        output_dir=tempfile.mkdtemp())
    output = wf.run(wfdoc)
    assert 'zostoga_mon_inmcm4_rcp45_r1i1p1_20850116-21001216.nc' in output[0]


def test_workflow_runner_tree():
    wf = workflow.WorkflowRunner(
        output_dir=tempfile.mkdtemp())
    output = wf.run(TREE_WF)
    assert 'tas_mon_HadGEM2-ES_rcp85_r1i1p1_20850116-21201216.nc' in output[0]
