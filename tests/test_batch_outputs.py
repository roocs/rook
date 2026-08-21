from datetime import timedelta
from pathlib import Path

import numpy as np
import xarray as xr
from clisops.utils.dataset_utils import open_xr_dataset

from rook.batch import outputs as batch_outputs


def write_batch(
    path,
    start,
    periods=3,
    calendar="standard",
    with_bounds=False,
    lat=(0.0, 1.0),
    compressed=False,
):
    time = xr.date_range(
        start,
        periods=periods,
        freq="D",
        use_cftime=True,
        calendar=calendar,
    )
    dataset = xr.Dataset(
        {
            "tas": (
                ("time", "lat", "lon"),
                np.arange(periods * 4, dtype="float32").reshape(periods, 2, 2),
            )
        },
        coords={"time": time, "lat": list(lat), "lon": [10.0, 11.0]},
        attrs={"project_id": "unknown"},
    )
    if with_bounds:
        dataset["time_bnds"] = (
            ("time", "bnds"),
            np.array([[value, value + timedelta(days=1)] for value in time]),
        )
        dataset.time.attrs["bounds"] = "time_bnds"
    encoding = (
        {"tas": {"zlib": True, "complevel": 1, "shuffle": True}} if compressed else None
    )
    dataset.to_netcdf(path, engine="h5netcdf", encoding=encoding)
    return path


def merge_outputs(inputs, **overrides):
    options = {
        "file_namer": "simple",
        "output_type": "netcdf",
        "merge_outputs": True,
        "merge_target_bytes": 1024**2,
        "max_output_bytes": 2 * 1024**2,
    }
    options.update(overrides)
    return batch_outputs.merge_batch_outputs([str(path) for path in inputs], **options)


def test_small_batch_outputs_are_merged_and_inputs_remain(tmp_path):
    inputs = [
        write_batch(tmp_path / "batch-1.nc", "2000-01-01"),
        write_batch(tmp_path / "batch-2.nc", "2000-01-04"),
    ]

    result = merge_outputs(inputs)

    assert len(result) == 1
    assert Path(result[0]).is_file()
    assert all(path.exists() for path in inputs)
    with open_xr_dataset(result[0]) as dataset:
        assert dataset.time.size == 6
        assert str(dataset.time.values[0]).startswith("2000-01-01")
        assert str(dataset.time.values[-1]).startswith("2000-01-06")


def test_batches_larger_than_merge_target_remain_separate(tmp_path):
    inputs = [
        write_batch(tmp_path / "batch-1.nc", "2000-01-01"),
        write_batch(tmp_path / "batch-2.nc", "2000-01-04"),
    ]
    batch_size = inputs[0].stat().st_size

    result = merge_outputs(inputs, merge_target_bytes=batch_size)

    assert result == [str(path) for path in inputs]
    assert all(path.is_file() for path in inputs)


def test_max_output_size_caps_estimated_merge_size(tmp_path):
    inputs = [
        write_batch(tmp_path / "batch-1.nc", "2000-01-01"),
        write_batch(tmp_path / "batch-2.nc", "2000-01-04"),
    ]

    result = merge_outputs(
        inputs,
        merge_target_bytes=2 * inputs[0].stat().st_size,
        max_output_bytes=inputs[0].stat().st_size,
    )

    assert result == [str(path) for path in inputs]


def test_merge_returns_multiple_bounded_groups_in_time_order(tmp_path):
    inputs = [
        write_batch(tmp_path / f"batch-{index}.nc", f"2000-01-{day:02d}")
        for index, day in enumerate((1, 4, 7, 10), start=1)
    ]
    batch_size = inputs[0].stat().st_size

    result = merge_outputs(inputs, merge_target_bytes=2 * batch_size)

    assert len(result) == 2
    assert all(path.exists() for path in inputs)
    with open_xr_dataset(result[0]) as first:
        assert str(first.time.values[0]).startswith("2000-01-01")
        assert str(first.time.values[-1]).startswith("2000-01-06")
    with open_xr_dataset(result[1]) as second:
        assert str(second.time.values[0]).startswith("2000-01-07")
        assert str(second.time.values[-1]).startswith("2000-01-12")


def test_merge_plan_uses_each_output_size(tmp_path):
    outputs = [tmp_path / f"batch-{index}.nc" for index in range(1, 4)]
    for output, size in zip(outputs, (10, 90, 10), strict=True):
        output.write_bytes(b"x" * size)

    groups = batch_outputs._plan_merges(
        outputs,
        enabled=True,
        output_type="netcdf",
        target_size=100,
    )

    assert groups == [outputs[:2], outputs[2:]]


def test_merge_preserves_360_day_time_bounds(tmp_path):
    inputs = [
        write_batch(
            tmp_path / "batch-1.nc",
            "2000-02-27",
            calendar="360_day",
            with_bounds=True,
        ),
        write_batch(
            tmp_path / "batch-2.nc",
            "2000-02-30",
            calendar="360_day",
            with_bounds=True,
        ),
    ]

    result = merge_outputs(inputs)

    with open_xr_dataset(result[0]) as dataset:
        assert dataset.time.dt.calendar == "360_day"
        assert dataset.time.size == 6
        assert dataset.time_bnds.shape == (6, 2)
        assert dataset.time_bnds.values[0, 0] == dataset.time.values[0]
        assert dataset.time_bnds.values[-1, 0] == dataset.time.values[-1]


def test_merge_preserves_decadal_spatial_bounds_dimension_order(tmp_path):
    inputs = []
    for index, start in enumerate(("2000-01-01", "2001-01-01"), start=1):
        time = xr.date_range(
            start,
            periods=12,
            freq="MS",
            use_cftime=True,
            calendar="360_day",
        )
        dataset = xr.Dataset(
            {
                "tas": (
                    ("time", "realization", "lat", "lon"),
                    np.full((12, 2, 2, 2), index, dtype="float32"),
                ),
                "lat_bnds": (
                    ("time", "realization", "lat", "bnds"),
                    np.broadcast_to(
                        np.array([[-0.5, 0.5], [0.5, 1.5]]),
                        (12, 2, 2, 2),
                    ),
                ),
                "lon_bnds": (
                    ("time", "realization", "lon", "bnds"),
                    np.broadcast_to(
                        np.array([[9.5, 10.5], [10.5, 11.5]]),
                        (12, 2, 2, 2),
                    ),
                ),
            },
            coords={
                "time": time,
                "realization": [1, 2],
                "lat": [0.0, 1.0],
                "lon": [10.0, 11.0],
            },
            attrs={"project_id": "CMIP6"},
        )
        path = tmp_path / f"decadal-{index}.nc"
        dataset.to_netcdf(path, engine="h5netcdf")
        inputs.append(path)

    result = merge_outputs(inputs)

    with open_xr_dataset(result[0]) as dataset:
        assert dataset.sizes["time"] == 24
        assert dataset.tas.values[:12].max() == 1
        assert dataset.tas.values[12:].min() == 2
        assert dataset.lat_bnds.dims == ("time", "realization", "lat", "bnds")
        assert dataset.lon_bnds.dims == ("time", "realization", "lon", "bnds")


def test_merge_preserves_data_variable_compression(tmp_path):
    inputs = [
        write_batch(tmp_path / "batch-1.nc", "2000-01-01", compressed=True),
        write_batch(tmp_path / "batch-2.nc", "2000-01-04", compressed=True),
    ]

    result = merge_outputs(inputs)

    with xr.open_dataset(result[0], engine="h5netcdf") as dataset:
        assert dataset.tas.encoding["zlib"] is True
        assert dataset.tas.encoding["complevel"] == 1
        assert dataset.tas.encoding["shuffle"] is True


def test_merge_failure_returns_all_original_batch_outputs(tmp_path, monkeypatch):
    inputs = [
        write_batch(tmp_path / "batch-1.nc", "2000-01-01"),
        write_batch(tmp_path / "batch-2.nc", "2000-01-04"),
    ]

    def fail_merge(_paths):
        raise RuntimeError("merge failed")

    monkeypatch.setattr(batch_outputs, "open_xr_dataset", fail_merge)

    result = merge_outputs(inputs)

    assert result == [str(path) for path in inputs]
    assert all(path.is_file() for path in inputs)


def test_merge_opens_outputs_with_bounded_chunks(tmp_path, monkeypatch):
    inputs = [
        write_batch(tmp_path / "batch-1.nc", "2000-01-01"),
        write_batch(tmp_path / "batch-2.nc", "2000-01-04"),
    ]
    opened_with = []
    original_open = batch_outputs.open_xr_dataset

    def recording_open(paths, **kwargs):
        opened_with.append(
            (paths, kwargs, batch_outputs.dask.config.get("scheduler", None))
        )
        return original_open(paths, **kwargs)

    monkeypatch.setattr(batch_outputs, "open_xr_dataset", recording_open)

    result = merge_outputs(inputs)

    assert len(result) == 1
    assert opened_with[0][0] == str(inputs[0])
    assert opened_with[0][1] == {}
    assert opened_with[1][1] == {"chunks": {"time": 3, "lat": 2, "lon": 2}}
    assert opened_with[1][2] == "single-threaded"


def test_merge_chunk_plan_splits_large_spatial_slices(monkeypatch):
    dask_array = __import__("dask.array", fromlist=["array"])
    dataset = xr.Dataset(
        {
            "tas": (
                ("time", "lat", "lon"),
                dask_array.empty((2, 10_000, 10_000), dtype="float64"),
            )
        }
    )
    monkeypatch.setattr(
        batch_outputs,
        "open_xr_dataset",
        lambda _path: dataset,
    )

    chunks = batch_outputs._bounded_chunks(Path("large.nc"))

    chunk_bytes = 8 * chunks["time"] * chunks["lat"] * chunks["lon"]
    assert chunk_bytes <= batch_outputs.MERGE_CHUNK_BYTES
    assert chunks["lat"] < dataset.sizes["lat"]
    assert chunks["lon"] < dataset.sizes["lon"]


def test_merging_can_be_disabled_without_opening_outputs(tmp_path):
    inputs = [str(tmp_path / "missing-1.nc"), str(tmp_path / "missing-2.nc")]

    assert (
        batch_outputs.merge_batch_outputs(
            inputs,
            file_namer="standard",
            output_type="netcdf",
            merge_outputs=False,
            merge_target_bytes=200_000_000,
            max_output_bytes=2_000_000_000,
        )
        == inputs
    )
