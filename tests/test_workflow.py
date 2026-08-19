import logging

from rook import workflow


class TestWorkflowTree:

    TREE_WF = "subset_wf_1.json"

    def test_validate_tree_wf(self, tmp_path, resource_file):
        wfdoc = workflow.load_wfdoc(resource_file(self.TREE_WF))
        wf = workflow.Workflow(output_dir=tmp_path)
        assert wf.validate(wfdoc) is True

    def test_replace_inputs(self, resource_file):
        wfdoc = workflow.load_wfdoc(resource_file(self.TREE_WF))
        steps = workflow.replace_inputs(wfdoc)
        assert steps["subset_tas"]["in"]["collection"] == [
            "cmip5.output1.MOHC.HadGEM2-ES.rcp85.mon.atmos.Amon.r1i1p1.latest.tas"
        ]

    def test_build_tree(self, resource_file):
        wfdoc = workflow.load_wfdoc(resource_file(self.TREE_WF))
        tree = workflow.build_tree(wfdoc)
        assert list(tree.edges) == [
            ("root", "output"),
            ("output", "average_tas"),
            ("average_tas", "subset_tas"),
        ]


def test_run_step_dispatches_registered_workflow_operation(tmp_path):
    calls = {}
    wf = workflow.Workflow(output_dir=tmp_path)

    class FakeOperation:
        def call(self, inputs):
            calls["operation_inputs"] = inputs
            return ["result.nc"]

    class FakeProvenance:
        def add_operator(self, step_id, inputs, collection, result):
            calls["provenance"] = (step_id, inputs, collection, result)

    wf.operations = {"subset": FakeOperation()}
    wf.prov = FakeProvenance()
    step = {
        "run": "subset",
        "in": {"collection": ["initial.nc"], "time": "2000/2001"},
    }

    result = wf._run_step("subset_step", step, {"collection": ["previous.nc"]})

    assert result == ["result.nc"]
    assert calls["operation_inputs"] == {
        "collection": ["previous.nc"],
        "time": "2000/2001",
    }
    assert step["in"]["collection"] == ["initial.nc"]
    assert calls["provenance"] == (
        "subset_step",
        calls["operation_inputs"],
        ["previous.nc"],
        ["result.nc"],
    )


def test_subset_selection_is_pushed_into_upstream_concat(tmp_path):
    calls = []
    wf = workflow.Workflow(output_dir=tmp_path)

    class FakeOperation:
        def __init__(self, name):
            self.name = name

        def call(self, inputs):
            calls.append((self.name, dict(inputs)))
            return [f"{self.name}.nc"]

    class FakeProvenance:
        def add_operator(self, *_args):
            pass

    wf.operations = {
        "concat": FakeOperation("concat"),
        "subset": FakeOperation("subset"),
    }
    wf.prov = FakeProvenance()
    document = {
        "doc": "decadal temporal pushdown",
        "inputs": {"ds": ["realization-1", "realization-2"]},
        "outputs": {"output": "subset/output"},
        "steps": {
            "concat": {
                "run": "concat",
                "in": {
                    "collection": "inputs/ds",
                    "dims": "realization",
                },
            },
            "subset": {
                "run": "subset",
                "in": {
                    "collection": "concat/output",
                    "time": "1962/1962",
                    "time_components": "month:aug|year:1962",
                    "area": "-10,35,30,70",
                },
            },
        },
    }

    result = wf._run(document)

    assert result == ["subset.nc"]
    assert calls[0] == (
        "concat",
        {
            "collection": ["realization-1", "realization-2"],
            "dims": "realization",
            "time": "1962/1962",
            "time_components": "month:aug|year:1962",
            "area": "-10,35,30,70",
        },
    )
    assert calls[1] == (
        "subset",
        {
            "collection": ["concat.nc"],
            "time": "1962/1962",
            "time_components": "month:aug|year:1962",
            "area": "-10,35,30,70",
        },
    )


def test_subset_pushdown_respects_average_dimensions():
    hint = {
        "time": "1962/1962",
        "time_components": "month:aug",
        "area": "-10,35,30,70",
    }

    assert (
        workflow._subset_pushdown_for_upstream(
            {"run": "average", "in": {"dims": ["realization"]}}, hint
        )
        == hint
    )
    assert workflow._subset_pushdown_for_upstream(
        {"run": "average", "in": {"dims": ["time"]}}, hint
    ) == {"area": "-10,35,30,70"}
    assert workflow._subset_pushdown_for_upstream(
        {"run": "average", "in": {"dims": ["latitude", "longitude"]}},
        hint,
    ) == {"time": "1962/1962", "time_components": "month:aug"}


def test_load_wfdoc_inline_document_does_not_warn_about_file_check(caplog):
    data = '{"doc": "' + ("x" * 300) + '", "steps": {}}'

    caplog.set_level(logging.WARNING)
    wfdoc = workflow.load_wfdoc(data)

    assert wfdoc["doc"] == "x" * 300
    assert "is_file check failed" not in caplog.text


def test_run_wf_cmip6_subset_average(tmp_path, resource_file):
    wfdoc = resource_file("wf_cmip6_subset_average.json")
    wf = workflow.WorkflowRunner(output_dir=tmp_path)
    output = wf.run(wfdoc)
    assert (
        "rlds_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_19850101-20140101_avg-year.nc"
        in output[0]
    )


def test_wf_average_latlon_cmip6(tmp_path, resource_file):
    wfdoc = resource_file("wf_average_latlon_cmip6.json")
    wf = workflow.WorkflowRunner(output_dir=tmp_path)
    output = wf.run(wfdoc)
    # print(output)
    assert (
        "rlds_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_19850116-20141216_avg-xy.nc"
        in output[0]
    )


def test_wf_c3s_cmip6_collection_only(tmp_path, resource_file):
    wfdoc = resource_file("wf_c3s_cmip6_subset_collection_only.json")
    wf = workflow.WorkflowRunner(output_dir=tmp_path)
    output = wf.run(wfdoc)
    expected_url = (
        "https://data.mips.climate.copernicus.eu/thredds/fileServer/esg_c3s-cmip6/"
        "CMIP/SNU/SAM0-UNICON/historical/r1i1p1f1/day/pr/gn/v20190323/"
        "pr_day_SAM0-UNICON_historical_r1i1p1f1_gn_18500101-18501231.nc"
    )
    assert output[0] == expected_url


def test_wf_c3s_cmip6_original_files(tmp_path, resource_file):
    wfdoc = resource_file("wf_c3s_cmip6_subset_original_files.json")
    wf = workflow.WorkflowRunner(output_dir=tmp_path)
    output = wf.run(wfdoc)
    expected_url = (
        "https://data.mips.climate.copernicus.eu/thredds/fileServer/esg_c3s-cmip6/"
        "CMIP/SNU/SAM0-UNICON/historical/r1i1p1f1/day/pr/gn/v20190323/"
        "pr_day_SAM0-UNICON_historical_r1i1p1f1_gn_18500101-18501231.nc"
    )
    assert expected_url in output
