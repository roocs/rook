import os
import tempfile

import pytest

from rook import workflow

from .common import resource_file

TREE_WF = resource_file("subset_wf_1.json")
TREE_WF_2 = resource_file("subset_wf_2.json")
TREE_WF_5 = resource_file("subset_wf_5.json")


def test_validate_tree_wf(tmp_path):
    wfdoc = workflow.load_wfdoc(TREE_WF)
    wf = workflow.Workflow(output_dir=tmp_path)
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


def test_run_tree_wf(tmp_path):
    wf = workflow.WorkflowRunner(output_dir=tmp_path)
    output = wf.run(TREE_WF)
    assert "tas_mon_HadGEM2-ES_rcp85_r1i1p1_20850101-21200101_avg-year.nc" in output[0]


def test_run_wf_cmip6_subset_average(tmp_path):
    wfdoc = resource_file("wf_cmip6_subset_average.json")
    wf = workflow.WorkflowRunner(output_dir=tmp_path)
    output = wf.run(wfdoc)
    assert (
        "rlds_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_19850101-20140101_avg-year.nc"
        in output[0]
    )


def test_wf_average_latlon_cmip6(tmp_path):
    wfdoc = resource_file("wf_average_latlon_cmip6.json")
    wf = workflow.WorkflowRunner(output_dir=tmp_path)
    output = wf.run(wfdoc)
    # print(output)
    assert (
        "rlds_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_19850116-20141216_avg-xy.nc"
        in output[0]
    )


def test_wf_c3s_cmip6_collection_only(tmp_path):
    wfdoc = resource_file("wf_c3s_cmip6_subset_collection_only.json")
    wf = workflow.WorkflowRunner(output_dir=tmp_path)
    output = wf.run(wfdoc)
    expected_url = (
        "https://data.mips.copernicus-climate.eu/thredds/fileServer/esg_c3s-cmip6/"
        "CMIP/SNU/SAM0-UNICON/historical/r1i1p1f1/day/pr/gn/v20190323/"
        "pr_day_SAM0-UNICON_historical_r1i1p1f1_gn_18500101-18501231.nc"
    )
    assert output[0] == expected_url


def test_wf_c3s_cmip6_original_files(tmp_path):
    wfdoc = resource_file("wf_c3s_cmip6_subset_original_files.json")
    wf = workflow.WorkflowRunner(output_dir=tmp_path)
    output = wf.run(wfdoc)
    expected_url = (
        "https://data.mips.copernicus-climate.eu/thredds/fileServer/esg_c3s-cmip6/"
        "CMIP/SNU/SAM0-UNICON/historical/r1i1p1f1/day/pr/gn/v20190323/"
        "pr_day_SAM0-UNICON_historical_r1i1p1f1_gn_18500101-18501231.nc"
    )
    assert expected_url in output
