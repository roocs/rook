import os
import tempfile

import pytest

from rook import workflow

from .common import resource_file

TREE_WF = resource_file("subset_wf_1.json")
TREE_WF_2 = resource_file("subset_wf_2.json")
TREE_WF_3 = resource_file("subset_wf_3.json")
TREE_WF_5 = resource_file("subset_wf_5.json")
TREE_WF_6 = resource_file("subset_wf_6.json")


def test_validate_tree_wf():
    wfdoc = workflow.load_wfdoc(TREE_WF)
    wf = workflow.TreeWorkflow(output_dir=tempfile.mkdtemp())
    assert wf.validate(wfdoc) is True


def test_replace_inputs():
    wfdoc = workflow.load_wfdoc(TREE_WF)
    steps = workflow.replace_inputs(wfdoc)
    assert steps["subset_tas"]["in"]["collection"] == [
        "cmip5.output1.MOHC.HadGEM2-ES.rcp85.mon.atmos.Amon.r1i1p1.latest.tas"
    ]


def test_build_tree():
    wfdoc = workflow.load_wfdoc(TREE_WF)
    tree = workflow.build_tree(wfdoc)
    assert list(tree.edges) == [
        ("root", "output"),
        ("output", "average_tas"),
        ("average_tas", "subset_tas"),
    ]


def test_run_tree_wf():
    wf = workflow.WorkflowRunner(output_dir=tempfile.mkdtemp())
    output = wf.run(TREE_WF)
    assert "tas_mon_HadGEM2-ES_rcp85_r1i1p1_avg-t.nc" in output[0]


def test_run_tree_wf_2():
    wf = workflow.WorkflowRunner(output_dir=tempfile.mkdtemp())
    output = wf.run(TREE_WF_2)
    assert "tas_mon_HadGEM2-ES_rcp85_r1i1p1_avg-t" in output[0]


@pytest.mark.skip(reason="Uses Diff operator - not implemented.")
def test_run_tree_wf_3():
    wf = workflow.WorkflowRunner(output_dir=tempfile.mkdtemp())
    output = wf.run(TREE_WF_3)
    assert "zostoga_mon_inmcm4_rcp45_r1i1p1_20850116-21001216.nc" in output[0]


def test_run_wf_cmip6_subset_average():
    wfdoc = resource_file("wf_cmip6_subset_average.json")
    wf = workflow.WorkflowRunner(output_dir=tempfile.mkdtemp())
    output = wf.run(wfdoc)
    assert "rlds_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_avg-t.nc" in output[0]


def test_run_tree_wf_5():
    wf = workflow.WorkflowRunner(output_dir=tempfile.mkdtemp())
    output = wf.run(TREE_WF_5)
    assert "rlds_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_avg-t.nc" in output[0]


@pytest.mark.skip(reason="Uses Diff operator - not implemented.")
def test_run_tree_wf_6():
    wf = workflow.WorkflowRunner(output_dir=tempfile.mkdtemp())
    output = wf.run(TREE_WF_6)
    assert (
        "https://data.mips.copernicus-climate.eu/thredds/fileServer/esg_c3s-cmip6"
        in output[0]
    )
    assert "zostoga_mon_inmcm4_rcp45_r1i1p1_20850116-21001216.nc" in output[0]


def test_wf_c3s_cmip6_collection_only():
    wfdoc = resource_file("wf_c3s_cmip6_subset_collection_only.json")
    wf = workflow.WorkflowRunner(output_dir=tempfile.mkdtemp())
    output = wf.run(wfdoc)
    expected_url = (
        "https://data.mips.copernicus-climate.eu/thredds/fileServer/esg_c3s-cmip6/"
        "CMIP/SNU/SAM0-UNICON/historical/r1i1p1f1/day/pr/gn/v20190323/"
        "pr_day_SAM0-UNICON_historical_r1i1p1f1_gn_18500101-18501231.nc"
    )
    assert output[0] == expected_url


def test_wf_c3s_cmip6_original_files():
    wfdoc = resource_file("wf_c3s_cmip6_subset_original_files.json")
    wf = workflow.WorkflowRunner(output_dir=tempfile.mkdtemp())
    output = wf.run(wfdoc)
    expected_url = (
        "https://data.mips.copernicus-climate.eu/thredds/fileServer/esg_c3s-cmip6/"
        "CMIP/SNU/SAM0-UNICON/historical/r1i1p1f1/day/pr/gn/v20190323/"
        "pr_day_SAM0-UNICON_historical_r1i1p1f1_gn_18500101-18501231.nc"
    )
    assert output[0] == expected_url
