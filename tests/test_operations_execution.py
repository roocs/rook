import logging

from clisops.utils.file_utils import FileMapper
from clisops.parameter.time_parameter import TimeParameter
import xarray as xr

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
    estimate_timesteps_per_year,
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
    assert Subset.calculate is TimeBatchingOperation.calculate
    assert issubclass(Subset, SubsetTimeBatchingOperation)


def test_timestep_estimate_extrapolates_partial_time_axes():
    daily = xr.DataArray(
        xr.date_range("2000-06-01", periods=30, freq="D", use_cftime=True),
        dims="time",
    )
    three_hourly = xr.DataArray(
        xr.date_range("2000-06-01", periods=30, freq="3h", use_cftime=True),
        dims="time",
    )
    monthly = xr.DataArray(
        xr.date_range("2000-06-01", periods=12, freq="MS", use_cftime=True),
        dims="time",
    )

    assert estimate_timesteps_per_year(daily, daily.dt.calendar) == 365
    assert estimate_timesteps_per_year(three_hourly, three_hourly.dt.calendar) == 2922
    assert estimate_timesteps_per_year(monthly, monthly.dt.calendar) == 12


class FakeTimeCoordinate:
    class YearValues:
        def __init__(self, values):
            self.values = values

    class DatetimeAccessor:
        def __init__(self, calendar, years):
            self.calendar = calendar
            self.year = FakeTimeCoordinate.YearValues(years)

    def __init__(self, calendar="standard", timesteps_per_year=365):
        self.size = timesteps_per_year
        self.dt = self.DatetimeAccessor(calendar, [2000] * timesteps_per_year)


class FakeSubsetDataset:
    def __init__(self, source=None, calendar="standard", timesteps_per_year=365):
        self.source = source
        self.time = FakeTimeCoordinate(calendar, timesteps_per_year)
        self.attrs = {}
        self.closed = False

    def close(self):
        self.closed = True


def make_recording_subset(
    monkeypatch,
    time,
    batching_config=None,
    timesteps_per_year=365,
    calendar="standard",
):
    calls = []
    opened_sources = []
    operation = object.__new__(Subset)
    operation.params = {
        "time": TimeParameter(time),
        "area": "0,0,10,10",
        "time_components": "month:01,02",
        "output_dir": "/tmp/output",
    }
    start, end = operation.params["time"].get_bounds()
    paths = [
        f"/data/input_{year}.nc" for year in range(int(start[:4]), int(end[:4]) + 1)
    ]
    operation.collection = (DatasetSource("project.dataset", paths),)
    operation._file_namer = "standard"
    operation._split_method = "time:auto"
    operation._output_dir = "/tmp/output"
    operation._output_type = "netcdf"
    if batching_config is None:
        batching_config = {
            "target_timesteps": 2000,
            "min_batch_years": 1,
            "max_batch_years": 10,
        }

    def fake_open_dataset(source):
        opened_sources.append(source)
        return FakeSubsetDataset(
            source,
            calendar=calendar,
            timesteps_per_year=timesteps_per_year,
        )

    def fake_normalise(sources):
        return {source.key: fake_open_dataset(source) for source in sources}

    def fake_process(_func, collection, **params):
        bounds = params["time"].get_bounds()
        calls.append((collection, bounds, dict(params)))
        return [f"subset-{len(calls)}.nc"]

    monkeypatch.setattr(operation_base, "process", fake_process)
    monkeypatch.setattr(time_batching_mod, "open_dataset", fake_open_dataset)
    monkeypatch.setattr(operation_base.normalise, "normalise", fake_normalise)
    monkeypatch.setattr(
        time_batching_mod.config, "get_subset_batching_config", lambda: batching_config
    )
    return operation, calls, opened_sources


def calculate_outputs(operation):
    result = operation.calculate()
    return next(iter(result._results.values()))


def test_subset_request_fitting_one_batch_uses_existing_processing_path(monkeypatch):
    operation, calls, _opened = make_recording_subset(
        monkeypatch, "2000-01-01/2004-12-31"
    )
    original_time = operation.params["time"]

    outputs = calculate_outputs(operation)

    assert outputs == ["subset-1.nc"]
    assert len(calls) == 1
    assert calls[0][2]["time"] is original_time


def test_subset_long_daily_request_runs_consecutive_batches(monkeypatch):
    operation, calls, opened = make_recording_subset(
        monkeypatch, "2000-01-01/2012-08-17T12:34:56"
    )

    outputs = calculate_outputs(operation)

    assert outputs == ["subset-1.nc", "subset-2.nc", "subset-3.nc"]
    assert [call[1] for call in calls] == [
        ("2000-01-01T00:00:00", "2004-12-31T23:59:59"),
        ("2005-01-01T00:00:00", "2009-12-31T23:59:59"),
        ("2010-01-01T00:00:00", "2012-08-17T12:34:56"),
    ]
    assert all(call[2]["area"] == "0,0,10,10" for call in calls)
    assert all(call[2]["time_components"] == "month:01,02" for call in calls)
    assert [len(source.paths) for source in opened[1:]] == [5, 5, 3]
    assert all(call[0].closed is True for call in calls)


def test_subset_century_request_opens_only_each_batch_files(monkeypatch):
    operation, calls, opened = make_recording_subset(monkeypatch, "2015/2100")
    messages = []

    class MessageHandler(logging.Handler):
        def emit(self, record):
            messages.append(record.getMessage())

    handler = MessageHandler()
    time_batching_mod.logger.addHandler(handler)
    previous_disable_level = logging.root.manager.disable
    logging.disable(logging.NOTSET)

    try:
        outputs = calculate_outputs(operation)
    finally:
        logging.disable(previous_disable_level)
        time_batching_mod.logger.removeHandler(handler)

    assert len(outputs) == 18
    assert len(calls) == 18
    assert len(opened[0].paths) == 1
    assert [len(source.paths) for source in opened[1:]] == [5] * 17 + [1]
    assert any(
        "batching plan" in message and "batches=18" in message for message in messages
    )
    assert any(
        "batch 18/18" in message and "1 source file(s)" in message
        for message in messages
    )


def test_subset_higher_frequency_data_uses_shorter_batches(monkeypatch):
    operation, calls, _opened = make_recording_subset(
        monkeypatch,
        "2000-01-01/2006-12-31",
        timesteps_per_year=2920,
    )

    calculate_outputs(operation)

    assert [call[1] for call in calls] == [
        (f"{year}-01-01T00:00:00", f"{year}-12-31T23:59:59")
        for year in range(2000, 2007)
    ]


def test_subset_low_frequency_data_uses_maximum_batch_years(monkeypatch):
    operation, calls, _opened = make_recording_subset(
        monkeypatch, "2000-01-01/2025-12-31", timesteps_per_year=12
    )

    calculate_outputs(operation)

    assert [call[1] for call in calls] == [
        ("2000-01-01T00:00:00", "2009-12-31T23:59:59"),
        ("2010-01-01T00:00:00", "2019-12-31T23:59:59"),
        ("2020-01-01T00:00:00", "2025-12-31T23:59:59"),
    ]


def test_subset_timestep_batch_configuration_can_be_overridden(monkeypatch):
    operation, calls, _opened = make_recording_subset(
        monkeypatch,
        "2000-01-01/2006-12-31",
        batching_config={
            "target_timesteps": 1000,
            "min_batch_years": 2,
            "max_batch_years": 4,
        },
    )

    calculate_outputs(operation)

    assert [call[1] for call in calls] == [
        ("2000-01-01T00:00:00", "2002-12-31T23:59:59"),
        ("2003-01-01T00:00:00", "2005-12-31T23:59:59"),
        ("2006-01-01T00:00:00", "2006-12-31T23:59:59"),
    ]


def test_subset_batches_use_dataset_calendar(monkeypatch):
    operation, calls, _opened = make_recording_subset(
        monkeypatch, "2000-02-30/2006-02-30", calendar="360_day"
    )

    calculate_outputs(operation)

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
