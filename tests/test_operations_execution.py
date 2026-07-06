from clisops.utils.file_utils import FileMapper

from rook.director.planning import WorkflowFiles
from rook.io.datasets import DatasetSource
import rook.operations.execution as execution_mod
from rook.operations.average import Average, AverageShape, AverageTime
from rook.operations import Operator
from rook.operations.base import Operation, is_prepared_dataset_collection
from rook.operations.regrid import Regrid
from rook.operations.subset import Subset


def recording_operator(output_dir):
    runner_inputs = {}

    def runner(inputs):
        runner_inputs["value"] = inputs
        return ["processed.nc"]

    operator = Operator(output_dir, prefix="recording", runner=runner)
    operator.runner_inputs = runner_inputs
    return operator


class RecordingOperation(Operation):
    def get_operation_callable(self):
        raise NotImplementedError


def fail_planned_request_executor(*_args, **_kwargs):
    raise AssertionError("planned request executor should not be called")


def test_workflow_operator_factory_keeps_prefix_and_runner(tmp_path):
    operator = execution_mod.make_workflow_operator("subset", tmp_path)

    assert operator.prefix == "subset"
    assert operator.runner is execution_mod.run_subset
    assert execution_mod.Subset(tmp_path).prefix == "subset"


def test_run_regrid_normalizes_custom_grid(monkeypatch):
    calls = {}

    class Result:
        file_uris = ["regridded.nc"]

    def fake_regrid(**kwargs):
        calls["kwargs"] = kwargs
        return Result()

    monkeypatch.setattr(execution_mod, "regrid", fake_regrid)

    result = execution_mod.run_regrid(
        {"collection": ["input.nc"], "grid": "custom", "custom_grid": "0.5 0.25"}
    )

    assert result == ["regridded.nc"]
    assert calls["kwargs"]["grid"] == (0.5, 0.25)
    assert "custom_grid" not in calls["kwargs"]


def test_direct_file_collection_is_processed_without_director(tmp_path, monkeypatch):
    source = tmp_path / "source.nc"
    source.touch()
    operator = recording_operator(tmp_path)
    monkeypatch.setattr(
        execution_mod, "execute_planned_request", fail_planned_request_executor
    )

    output_uris = operator.call(
        {
            "collection": [source.as_posix()],
            "apply_fixes": True,
            "original_files": True,
            "pre_checked": True,
        }
    )

    assert output_uris == ["processed.nc"]
    runner_inputs = operator.runner_inputs["value"]
    assert "apply_fixes" not in runner_inputs
    assert "original_files" not in runner_inputs
    assert "pre_checked" not in runner_inputs
    assert isinstance(runner_inputs["collection"], FileMapper)
    assert runner_inputs["output_dir"].startswith(tmp_path.as_posix())


def test_later_workflow_step_receives_previous_step_files(tmp_path, monkeypatch):
    first = tmp_path / "first.nc"
    second = tmp_path / "second.nc"
    first.touch()
    second.touch()
    operator = recording_operator(tmp_path)
    monkeypatch.setattr(
        execution_mod, "execute_planned_request", fail_planned_request_executor
    )

    output_uris = operator.call({"collection": [first.as_posix(), second.as_posix()]})

    assert output_uris == ["processed.nc"]
    assert isinstance(operator.runner_inputs["value"]["collection"], FileMapper)


def test_workflow_file_inputs_are_prepared_explicitly(tmp_path):
    first = tmp_path / "first.nc"
    second = tmp_path / "second.nc"
    first.touch()
    second.touch()
    args = {
        "collection": [first.as_posix(), second.as_posix()],
        "apply_fixes": True,
        "original_files": True,
        "pre_checked": True,
    }
    source = WorkflowFiles(files=args["collection"])

    runner_inputs = execution_mod.prepare_workflow_file_inputs(args, source)

    assert isinstance(runner_inputs["collection"], FileMapper)
    assert "apply_fixes" not in runner_inputs
    assert "original_files" not in runner_inputs
    assert "pre_checked" not in runner_inputs
    assert args["collection"] == [first.as_posix(), second.as_posix()]


def test_operation_accepts_prepared_dataset_sources(monkeypatch):
    prepared = DatasetSource(
        dataset_id="c3s-cmip6.example.dataset",
        paths="/data/c3s-cmip6.example.dataset.nc",
    )
    monkeypatch.setattr(
        "rook.operations.base.consolidate.consolidate",
        lambda collection, **_kwargs: collection.value,
    )

    assert is_prepared_dataset_collection([prepared]) is True
    assert is_prepared_dataset_collection([]) is False

    operation = RecordingOperation(collection=[prepared])

    assert operation.collection == (prepared,)


def test_operation_wrappers_accept_prepared_dataset_sources(monkeypatch):
    prepared = DatasetSource(
        dataset_id="c3s-cmip6.example.dataset",
        paths="/data/c3s-cmip6.example.dataset.nc",
    )
    monkeypatch.setattr(
        "rook.operations.base.consolidate.consolidate",
        lambda collection, **_kwargs: collection.value,
    )

    operations = [
        Subset(collection=[prepared], time="2015-01-01/2015-12-30"),
        Average(collection=[prepared], dims=["time"]),
        AverageShape(collection=[prepared], shape="shape.geojson"),
        AverageTime(collection=[prepared], freq="year"),
        Regrid(collection=[prepared], grid="1deg"),
    ]

    for operation in operations:
        assert operation.collection == (prepared,)
