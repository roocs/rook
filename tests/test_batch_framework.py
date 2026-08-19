import xarray as xr

from rook.batch import BatchProcessor, ConcatBatch, TimeBatch, TimeBatchPlanner


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

    daily_batches = TimeBatchPlanner(**config).plan(
        daily,
        start="2000-01-01T00:00:00",
        end="2012-12-31T23:59:59",
    )
    monthly_batches = TimeBatchPlanner(**config).plan(
        monthly,
        start="2000-01-01T00:00:00",
        end="2025-12-31T23:59:59",
    )

    assert [batch.start[:4] for batch in daily_batches] == ["2000", "2005", "2010"]
    assert [batch.start[:4] for batch in monthly_batches] == ["2000", "2010", "2020"]


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
        TimeBatchPlanner(
            target_timesteps=12,
            min_batch_years=1,
            max_batch_years=1,
        )
    )
    calls = []

    outputs = processor.process(
        time,
        lambda batch, index, total: calls.append((batch.start, batch.end, index, total))
        or [f"batch-{index}.nc"],
    )

    assert outputs == ["batch-1.nc", "batch-2.nc"]
    assert [call[2:] for call in calls] == [(1, 2), (2, 2)]
