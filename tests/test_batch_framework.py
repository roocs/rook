import xarray as xr

from rook.batch import (
    BatchProcessor,
    BaseBatchPlanner,
    ConcatBatch,
    ConcatBatchPlanner,
    SubsetBatchPlanner,
    TimeBatch,
    TimeBounds,
)


def test_time_batch_planner_preserves_adaptive_one_to_ten_year_bounds():
    daily = xr.DataArray(
        xr.date_range("2000-01-01", periods=366, freq="D", use_cftime=True),
        dims="time",
    )
    monthly = xr.DataArray(
        xr.date_range("2000-01-01", periods=24, freq="MS", use_cftime=True),
        dims="time",
    )
    config = {
        "target_timesteps": 2000,
        "min_batch_years": 1,
        "max_batch_years": 10,
    }

    planner = SubsetBatchPlanner(**config)

    daily_batches = planner.plan(
        daily,
        TimeBounds(
            "2000-01-01T00:00:00",
            "2012-12-31T23:59:59",
        ),
    )
    monthly_batches = planner.plan(
        monthly,
        TimeBounds(
            "2000-01-01T00:00:00",
            "2025-12-31T23:59:59",
        ),
    )

    assert [batch.start[:4] for batch in daily_batches] == ["2000", "2005", "2010"]
    assert [batch.start[:4] for batch in monthly_batches] == ["2000", "2010", "2020"]
    assert isinstance(planner, BaseBatchPlanner)


def test_subset_and_concat_planners_adapt_the_common_planning_mechanics():
    time = xr.DataArray(
        xr.date_range("2000-01-01", periods=24, freq="MS", use_cftime=True),
        dims="time",
    )
    config = {
        "target_timesteps": 12,
        "min_batch_years": 1,
        "max_batch_years": 1,
    }

    subset = SubsetBatchPlanner(**config)
    assert subset.plan(time, TimeBounds(None, "2001-12-31")) == []

    class RequestedTime:
        type = "interval"

        @staticmethod
        def get_bounds():
            return "2001-01-01T00:00:00", "2001-12-31T23:59:59"

    concat = ConcatBatchPlanner(**config)
    batches = concat.plan(
        [xr.Dataset(coords={"time": time})],
        RequestedTime(),
    )

    assert batches == [TimeBatch("2001-01-01T00:00:00", "2001-12-31T23:59:59")]
    assert isinstance(concat, BaseBatchPlanner)


def test_daily_concat_uses_yearly_batches_for_bounded_and_full_requests():
    time = xr.DataArray(
        xr.date_range("2000-01-01", "2006-12-31", freq="D", use_cftime=True),
        dims="time",
    )
    datasets = [xr.Dataset(coords={"time": time}) for _ in range(2)]
    concat = ConcatBatchPlanner(
        target_timesteps=365,
        min_batch_years=1,
        max_batch_years=1,
    )

    class SevenYearRequest:
        type = "interval"

        @staticmethod
        def get_bounds():
            return "2000-01-01T00:00:00", "2006-12-31T23:59:59"

    bounded = concat.plan(datasets, SevenYearRequest())
    unconstrained = concat.plan(datasets)

    assert [batch.start[:4] for batch in bounded] == [
        "2000",
        "2001",
        "2002",
        "2003",
        "2004",
        "2005",
        "2006",
    ]
    assert [batch.start[:4] for batch in unconstrained] == [
        batch.start[:4] for batch in bounded
    ]
    assert all(batch.start[:4] == batch.end[:4] for batch in bounded)
    assert all(batch.start[:4] == batch.end[:4] for batch in unconstrained)


def test_concat_request_shorter_than_one_year_stays_in_one_batch():
    time = xr.DataArray(
        xr.date_range("2000-03-01", "2000-08-31", freq="D", use_cftime=True),
        dims="time",
    )
    planner = ConcatBatchPlanner(
        target_timesteps=365,
        min_batch_years=1,
        max_batch_years=1,
    )

    assert planner.plan([xr.Dataset(coords={"time": time})]) == [
        TimeBatch("2000-03-01T00:00:00", "2000-08-31T00:00:00")
    ]


def test_concat_year_ceiling_does_not_change_subset_batching():
    time = xr.DataArray(
        xr.date_range("2000-01-01", "2006-12-31", freq="D", use_cftime=True),
        dims="time",
    )
    subset = SubsetBatchPlanner(
        target_timesteps=2000,
        min_batch_years=1,
        max_batch_years=10,
    )

    batches = subset.plan(
        time,
        TimeBounds("2000-01-01T00:00:00", "2006-12-31T23:59:59"),
    )

    assert [batch.start[:4] for batch in batches] == ["2000", "2005"]


def test_batch_processor_completes_each_callback_before_starting_the_next():
    events = []
    batches = [TimeBatch("2000", "2000"), TimeBatch("2001", "2001")]

    def process(batch, index, total):
        if index > 1:
            assert events[-1] == ("finish", index - 1)
        events.append(("start", index))
        events.append(("finish", index))
        return [batch.interval]

    outputs = BatchProcessor().execute(batches, process)

    assert outputs == ["2000/2000", "2001/2001"]
    assert events == [
        ("start", 1),
        ("finish", 1),
        ("start", 2),
        ("finish", 2),
    ]


def test_concat_batch_is_a_generic_time_batch_callback_processor():
    time = xr.DataArray(
        xr.date_range("2000-01-01", periods=24, freq="MS", use_cftime=True),
        dims="time",
    )
    processor = ConcatBatch(
        ConcatBatchPlanner(
            target_timesteps=12,
            min_batch_years=1,
            max_batch_years=1,
        )
    )
    calls = []

    datasets = [xr.Dataset(coords={"time": time}) for _ in range(2)]

    def process(combined, interval, index, total):
        calls.append(
            (
                combined.time.values[0].year,
                combined.sizes["time"],
                interval,
                index,
                total,
            )
        )
        return [f"batch-{index}.nc"]

    outputs = processor.process(
        datasets,
        dim="realization",
        operation=process,
    )

    assert outputs == ["batch-1.nc", "batch-2.nc"]
    assert [(call[0], call[1]) for call in calls] == [(2000, 12), (2001, 12)]
    assert [call[3:] for call in calls] == [(1, 2), (2, 2)]


def test_concat_batch_applies_dataset_selector_before_concat(monkeypatch):
    time = xr.date_range("1962-01-01", "1962-12-31", freq="D", use_cftime=True)
    datasets = [
        xr.Dataset({"tas": ("time", range(len(time)))}, coords={"time": time})
        for _ in range(2)
    ]
    processor = ConcatBatch(
        ConcatBatchPlanner(
            target_timesteps=365,
            min_batch_years=1,
            max_batch_years=1,
        )
    )
    events = []
    original_concat = xr.concat

    def select_august(dataset):
        events.append(("select", dataset.sizes["time"]))
        return dataset.isel(time=dataset.time.dt.month == 8)

    def concat(selected, dim):
        events.append(("concat", [dataset.sizes["time"] for dataset in selected]))
        return original_concat(selected, dim=dim)

    monkeypatch.setattr("rook.batch.concat.xr.concat", concat)

    outputs = processor.process(
        datasets,
        dim="realization",
        operation=lambda combined, _time, _index, _total: [combined.sizes["time"]],
        select_dataset=select_august,
    )

    assert outputs == [31]
    assert events == [("select", 365), ("select", 365), ("concat", [31, 31])]


def test_concat_batch_filters_irrelevant_batches_before_selection():
    time = xr.date_range("1960-01-01", "1964-12-31", freq="D", use_cftime=True)
    datasets = [xr.Dataset(coords={"time": time}) for _ in range(2)]
    processor = ConcatBatch(
        ConcatBatchPlanner(
            target_timesteps=365,
            min_batch_years=1,
            max_batch_years=1,
        )
    )
    selected_years = []

    def select(dataset):
        selected_years.append(int(dataset.time.dt.year.values[0]))
        return dataset

    outputs = processor.process(
        datasets,
        dim="realization",
        operation=lambda _combined, interval, _index, _total: [interval],
        select_dataset=select,
        include_batch=lambda batch: batch.start.startswith(("1961", "1963")),
    )

    assert [interval[:4] for interval in outputs] == ["1961", "1963"]
    assert selected_years == [1961, 1961, 1963, 1963]
