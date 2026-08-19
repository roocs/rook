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


def test_subset_selection_consumed_by_concat_becomes_pass_through(tmp_path):
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

    assert result == ["concat.nc"]
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
    assert len(calls) == 1


def _recording_workflow(tmp_path, document):
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
    result = wf._run(document)
    return calls, result


def _concat_subset_document(subset_inputs, concat_inputs=None):
    return {
        "doc": "physical concat subset rewrite",
        "inputs": {"ds": ["realization-1", "realization-2"]},
        "outputs": {"output": "subset/output"},
        "steps": {
            "concat": {
                "run": "concat",
                "in": {
                    "collection": "inputs/ds",
                    "dims": "realization",
                    **(concat_inputs or {}),
                },
            },
            "subset": {
                "run": "subset",
                "in": {"collection": "concat/output", **subset_inputs},
            },
        },
    }


def test_concat_subset_time_becomes_pass_through(tmp_path):
    calls, result = _recording_workflow(
        tmp_path,
        _concat_subset_document({"time": "1962/1962"}),
    )

    assert calls[0][1]["time"] == "1962/1962"
    assert len(calls) == 1
    assert result == ["concat.nc"]


def test_concat_subset_time_components_becomes_pass_through(tmp_path):
    calls, result = _recording_workflow(
        tmp_path,
        _concat_subset_document({"time_components": "month:aug|year:1962"}),
    )

    assert calls[0][1]["time_components"] == "month:aug|year:1962"
    assert len(calls) == 1
    assert result == ["concat.nc"]


def test_concat_subset_time_and_components_becomes_pass_through(tmp_path):
    calls, result = _recording_workflow(
        tmp_path,
        _concat_subset_document(
            {
                "time": "1962/1963",
                "time_components": "month:aug",
            }
        ),
    )

    assert calls[0][1]["time"] == "1962/1963"
    assert calls[0][1]["time_components"] == "month:aug"
    assert len(calls) == 1
    assert result == ["concat.nc"]


def test_default_output_controls_do_not_prevent_pass_through(tmp_path):
    calls, result = _recording_workflow(
        tmp_path,
        _concat_subset_document(
            {
                "time": "1962/1963",
                "output_type": "netcdf",
                "split_method": "time:auto",
                "file_namer": "standard",
                "ignore_undetected_dims": False,
                "original_files": False,
                "pre_checked": False,
            }
        ),
    )

    assert len(calls) == 1
    assert result == ["concat.nc"]


def test_concat_subset_time_and_area_passes_only_after_both_are_consumed(tmp_path):
    calls, result = _recording_workflow(
        tmp_path,
        _concat_subset_document({"time": "1962/1963", "area": "-10,35,30,70"}),
    )

    assert calls[0][1]["time"] == "1962/1963"
    assert calls[0][1]["area"] == "-10,35,30,70"
    assert len(calls) == 1
    assert result == ["concat.nc"]


def test_conflicting_concat_area_keeps_area_on_subset(tmp_path):
    calls, result = _recording_workflow(
        tmp_path,
        _concat_subset_document(
            {"time": "1962/1963", "area": "-10,35,30,70"},
            concat_inputs={"area": "0,35,30,70"},
        ),
    )

    assert calls[0][1]["time"] == "1962/1963"
    assert calls[0][1]["area"] == "0,35,30,70"
    assert calls[1][1] == {
        "collection": ["concat.nc"],
        "area": "-10,35,30,70",
    }
    assert result == ["subset.nc"]


def test_subset_without_compatible_concat_keeps_temporal_parameters(tmp_path):
    calls = []
    wf = workflow.Workflow(output_dir=tmp_path)

    class FakeSubset:
        def call(self, inputs):
            calls.append(dict(inputs))
            return ["subset.nc"]

    class FakeProvenance:
        def add_operator(self, *_args):
            pass

    wf.operations = {"subset": FakeSubset()}
    wf.prov = FakeProvenance()
    wf._run(
        {
            "doc": "ordinary subset",
            "inputs": {"ds": ["input.nc"]},
            "outputs": {"output": "subset/output"},
            "steps": {
                "subset": {
                    "run": "subset",
                    "in": {
                        "collection": "inputs/ds",
                        "time": "1962/1962",
                        "time_components": "month:aug|year:1962",
                    },
                }
            },
        }
    )

    assert calls[0]["time"] == "1962/1962"
    assert calls[0]["time_components"] == "month:aug|year:1962"


def test_conflicting_concat_time_does_not_consume_subset_time(tmp_path):
    calls, _result = _recording_workflow(
        tmp_path,
        _concat_subset_document(
            {"time": "1962/1962"},
            concat_inputs={"time": "1960/1961"},
        ),
    )

    assert calls[0][1]["time"] == "1960/1961"
    assert calls[1][1]["time"] == "1962/1962"


def test_explicit_output_option_keeps_real_subset_execution(tmp_path):
    calls, result = _recording_workflow(
        tmp_path,
        _concat_subset_document(
            {
                "time": "1962/1962",
                "output_type": "zarr",
            }
        ),
    )

    assert calls[0][1]["time"] == "1962/1962"
    assert calls[1] == (
        "subset",
        {"collection": ["concat.nc"], "output_type": "zarr"},
    )
    assert result == ["subset.nc"]


def test_unknown_subset_parameter_prevents_pass_through(tmp_path):
    calls, result = _recording_workflow(
        tmp_path,
        _concat_subset_document({"time": "1962/1962", "unknown_option": "value"}),
    )

    assert calls[1] == (
        "subset",
        {"collection": ["concat.nc"], "unknown_option": "value"},
    )
    assert result == ["subset.nc"]


def test_pass_through_returns_concat_paths_without_creating_subset_files(tmp_path):
    concat_files = [tmp_path / "1962.nc", tmp_path / "1963.nc"]
    concat_paths = [path.as_posix() for path in concat_files]
    subset_path = tmp_path / "subset.nc"
    provenance_steps = []
    wf = workflow.Workflow(output_dir=tmp_path)

    class FakeConcat:
        def call(self, _inputs):
            for path in concat_files:
                path.touch()
            return concat_paths

    class FailingSubset:
        def call(self, _inputs):
            subset_path.touch()
            raise AssertionError("pass-through must not call subset")

    class FakeProvenance:
        def add_operator(self, step_id, *_args):
            provenance_steps.append(step_id)

    wf.operations = {"concat": FakeConcat(), "subset": FailingSubset()}
    wf.prov = FakeProvenance()

    result = wf._run(_concat_subset_document({"time": "1962/1963"}))

    assert result == concat_paths
    assert not subset_path.exists()
    assert provenance_steps == ["concat", "subset"]


def test_unsupported_temporal_pushdown_keeps_subset_time(tmp_path):
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
        name: FakeOperation(name) for name in ("concat", "average", "subset")
    }
    wf.prov = FakeProvenance()
    document = _concat_subset_document({"time": "1962/1962"})
    document["steps"]["subset"]["in"]["collection"] = "average/output"
    document["steps"]["average"] = {
        "run": "average",
        "in": {"collection": "concat/output", "dims": ["time"]},
    }

    wf._run(document)

    assert "time" not in calls[0][1]
    assert calls[2][1]["time"] == "1962/1962"


def test_temporal_execution_rewrite_preserves_logical_result(tmp_path):
    dates = ["1961-08-01", "1962-07-01", "1962-08-01", "1962-08-02"]
    wf = workflow.Workflow(output_dir=tmp_path)

    class FilterOperation:
        def call(self, inputs):
            selected = list(inputs["collection"])
            if inputs.get("time") == "1962/1962":
                selected = [value for value in selected if value.startswith("1962-")]
            if inputs.get("time_components") == "month:aug|year:1962":
                selected = [value for value in selected if value.startswith("1962-08-")]
            return selected

    class FakeProvenance:
        def add_operator(self, *_args):
            pass

    wf.operations = {"concat": FilterOperation(), "subset": FilterOperation()}
    wf.prov = FakeProvenance()
    document = _concat_subset_document(
        {
            "time": "1962/1962",
            "time_components": "month:aug|year:1962",
        }
    )
    document["inputs"]["ds"] = dates

    assert wf._run(document) == ["1962-08-01", "1962-08-02"]


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
