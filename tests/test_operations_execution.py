from clisops.utils.file_utils import FileMapper
from clisops.parameter.time_parameter import TimeParameter
import pytest

from rook.pflow.sources import WorkflowFiles
from rook.io.datasets import DatasetSource
import rook.operations.execution as execution_mod
import rook.operations.time_batching as time_batching_mod
from rook.operations.average import Average, AverageShape, AverageTime
from rook.operations import Operator
from rook.operations.base import Operation, is_prepared_dataset_collection
import rook.operations.base as operation_base
from rook.operations.concat import Concat
from rook.operations.regrid import Regrid
from rook.operations.subset import Subset
from rook.operations.time_batching import (
    SubsetTimeBatchingOperation,
    TimeBatchingOperation,
)

BATCH_FREQUENCIES = frozenset(
    {"day", "6hr", "6hrpt", "3hr", "3hrpt", "1hr", "1hrcm", "1hrpt", "subhrpt"}
)


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


def fail_request_decision_executor(*_args, **_kwargs):
    raise AssertionError("request decision executor should not be called")


def test_workflow_operator_factory_keeps_prefix_and_runner(tmp_path):
    operator = execution_mod.make_workflow_operator("subset", tmp_path)

    assert operator.prefix == "subset"
    assert operator.runner is execution_mod.run_subset
    assert operator.allow_aligned_original_files is True
    assert execution_mod.Subset(tmp_path).prefix == "subset"

    concat_operator = execution_mod.make_workflow_operator("concat", tmp_path)
    assert concat_operator.allow_aligned_original_files is False


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


def test_direct_file_collection_is_processed_without_request_resolution(
    tmp_path, monkeypatch
):
    source = tmp_path / "source.nc"
    source.touch()
    operator = recording_operator(tmp_path)
    monkeypatch.setattr(
        execution_mod, "execute_resolved_request", fail_request_decision_executor
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
        execution_mod, "execute_resolved_request", fail_request_decision_executor
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
        Concat(collection=[prepared], dims="realization"),
        Regrid(collection=[prepared], grid="1deg"),
    ]

    for operation in operations:
        assert operation.collection == (prepared,)


def test_subset_uses_base_operation_calculate():
    assert Subset.calculate is Operation.calculate
    assert issubclass(Subset, SubsetTimeBatchingOperation)
    assert Subset._process_collection is TimeBatchingOperation._process_collection


class FakeTimeCoordinate:
    class DatetimeAccessor:
        def __init__(self, calendar):
            self.calendar = calendar

    def __init__(self, calendar="standard"):
        self.dt = self.DatetimeAccessor(calendar)


class FakeSubsetDataset:
    def __init__(self, calendar="standard", frequency="day"):
        self.time = FakeTimeCoordinate(calendar)
        self.attrs = {"frequency": frequency}


def make_recording_subset(
    monkeypatch,
    time,
    batch_size=5,
    batch_frequencies=BATCH_FREQUENCIES,
):
    calls = []
    operation = object.__new__(Subset)
    operation.params = {
        "time": TimeParameter(time),
        "area": "0,0,10,10",
        "time_components": "month:01,02",
        "output_dir": "/tmp/output",
    }

    def fake_process(_func, collection, **params):
        bounds = params["time"].get_bounds()
        calls.append((collection, bounds, dict(params)))
        return [f"subset-{len(calls)}.nc"]

    monkeypatch.setattr(operation_base, "process", fake_process)
    monkeypatch.setattr(
        time_batching_mod.config, "get_subset_time_batch_size", lambda: batch_size
    )
    monkeypatch.setattr(
        time_batching_mod.config,
        "get_batch_frequencies",
        lambda: batch_frequencies,
    )
    return operation, calls


def test_subset_request_fitting_one_batch_uses_existing_processing_path(monkeypatch):
    operation, calls = make_recording_subset(monkeypatch, "2000-01-01/2004-12-31")
    original_time = operation.params["time"]

    outputs = operation._process_collection(
        "project.model.day.variable", FakeSubsetDataset()
    )

    assert outputs == ["subset-1.nc"]
    assert len(calls) == 1
    assert calls[0][2]["time"] is original_time


def test_subset_long_daily_request_runs_consecutive_batches(monkeypatch):
    operation, calls = make_recording_subset(
        monkeypatch, "2000-01-01/2012-08-17T12:34:56"
    )

    outputs = operation._process_collection(
        "project.model.day.variable", FakeSubsetDataset()
    )

    assert outputs == ["subset-1.nc", "subset-2.nc", "subset-3.nc"]
    assert [call[1] for call in calls] == [
        ("2000-01-01T00:00:00", "2004-12-31T23:59:59"),
        ("2005-01-01T00:00:00", "2009-12-31T23:59:59"),
        ("2010-01-01T00:00:00", "2012-08-17T12:34:56"),
    ]
    assert all(call[2]["area"] == "0,0,10,10" for call in calls)
    assert all(call[2]["time_components"] == "month:01,02" for call in calls)


def test_subset_batch_size_is_configurable(monkeypatch):
    operation, calls = make_recording_subset(
        monkeypatch, "2000-01-01/2006-12-31", batch_size=3
    )

    operation._process_collection(
        "project.model.unrelated.variable",
        FakeSubsetDataset(frequency="3HR"),
    )

    assert [call[1] for call in calls] == [
        ("2000-01-01T00:00:00", "2002-12-31T23:59:59"),
        ("2003-01-01T00:00:00", "2005-12-31T23:59:59"),
        ("2006-01-01T00:00:00", "2006-12-31T23:59:59"),
    ]


def test_subset_monthly_request_is_not_batched(monkeypatch):
    operation, calls = make_recording_subset(monkeypatch, "2000-01-01/2020-12-31")

    operation._process_collection(
        "project.model.day.variable", FakeSubsetDataset(frequency="mon")
    )

    assert len(calls) == 1


@pytest.mark.parametrize(
    "frequency",
    ["day", "6hr", "6hrPt", "3hr", "3hrPt", "1hr", "1hrCM", "1hrPt", "subhrPt"],
)
def test_subset_configured_frequency_is_batched(monkeypatch, frequency):
    operation, calls = make_recording_subset(monkeypatch, "2000-01-01/2006-12-31")

    operation._process_collection(
        "project.identifier.without.frequency", FakeSubsetDataset(frequency=frequency)
    )

    assert len(calls) == 2


@pytest.mark.parametrize("frequency", ["mon", "Amon", "yr", "fx"])
def test_subset_noneligible_frequency_is_not_batched(monkeypatch, frequency):
    operation, calls = make_recording_subset(monkeypatch, "2000-01-01/2020-12-31")

    operation._process_collection(
        "project.identifier.contains.day", FakeSubsetDataset(frequency=frequency)
    )

    assert len(calls) == 1


def test_subset_batch_frequency_configuration_can_be_overridden(monkeypatch):
    operation, calls = make_recording_subset(
        monkeypatch,
        "2000-01-01/2006-12-31",
        batch_frequencies=frozenset({"custom"}),
    )

    operation._process_collection(
        "project.model.mon.variable", FakeSubsetDataset(frequency="CUSTOM")
    )

    assert len(calls) == 2


def test_subset_batches_use_dataset_calendar(monkeypatch):
    operation, calls = make_recording_subset(monkeypatch, "2000-02-30/2006-02-30")
    dataset = FakeSubsetDataset(calendar="360_day")

    operation._process_collection("project.model.day.variable", dataset)

    assert [call[1] for call in calls] == [
        ("2000-02-30T00:00:00", "2005-02-29T23:59:59"),
        ("2005-02-30T00:00:00", "2006-02-30T23:59:59"),
    ]


def test_base_operation_uses_configured_fix_provider_during_dataset_opening(
    monkeypatch,
):
    calls = []
    operation_dataset = object()

    monkeypatch.setattr(
        "rook.operations.base.consolidate.consolidate",
        lambda collection, **_kwargs: collection.value,
    )
    monkeypatch.setattr(
        operation_base.normalise,
        "normalise",
        lambda collection: calls.append(("normalise", collection))
        or {"dataset": operation_dataset},
    )
    monkeypatch.setattr(
        operation_base,
        "process",
        lambda func, collection, **params: calls.append(("process", collection, params))
        or ["result.nc"],
    )

    source = DatasetSource("dataset.id", "input.nc")

    result = Subset(collection=[source]).calculate()

    assert result.file_uris == []
    assert calls[0] == ("normalise", (source,))
    assert calls[1][0] == "process"
    assert calls[1][1] is operation_dataset
    assert calls[1][2]["output_type"] == "netcdf"
    assert calls[1][2]["output_dir"] is None
    assert calls[1][2]["split_method"] == "time:auto"
    assert calls[1][2]["file_namer"] == "standard"
