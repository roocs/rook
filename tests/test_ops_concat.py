import numpy as np
import xarray as xr

import rook.operations.concat as concat_mod
from rook.batch import ConcatBatch, ConcatBatchPlanner, TimeBatch
from rook.io.datasets import DatasetSource


def _concat_batch_inputs(datasets):
    collection = {str(index): (f"source-{index}.nc",) for index in range(len(datasets))}

    def open_dataset(dataset_id, _paths, _batch):
        return datasets[int(dataset_id)].copy(deep=False)

    return collection, open_dataset


def test_concat_dataset_paths_are_keyed_by_catalog_id(monkeypatch):
    sources = [
        DatasetSource("project.dataset", ["one.nc", "two.nc"]),
        DatasetSource(None, ["direct.nc"]),
    ]
    monkeypatch.setattr(concat_mod, "derive_ds_id", lambda _path: "derived.dataset")

    collection = concat_mod.dataset_paths_by_id(sources)

    assert list(collection) == ["project.dataset", "derived.dataset"]
    assert collection["project.dataset"] == ("one.nc", "two.nc")
    assert collection["derived.dataset"] == ("direct.nc",)


def test_apply_concat_calendar_fix_applies_decadal_calendar_fix():
    calls = []
    source = xr.Dataset(attrs={"source": "input"})

    class FakeProvider:
        def prepare(self, ds, *, context=None):
            calls.append(
                (
                    ds.attrs["source"],
                    context.dataset_id,
                    context.operation,
                    context.phase,
                )
            )
            return ds

    result = concat_mod.apply_concat_calendar_fix(
        source, FakeProvider(), dataset_id="decadal.dataset"
    )

    assert result is source
    assert calls == [("input", "decadal.dataset", "concat", "prepare")]


def test_concat_batch_paths_keeps_only_files_overlapping_batch():
    paths = (
        "psl_day_model_19610101-19611231.nc",
        "psl_day_model_19620101-19621231.nc",
        "psl_day_model_19630101-19631231.nc",
    )

    selected = concat_mod.concat_batch_paths(
        paths,
        TimeBatch("1962-01-01T00:00:00", "1962-12-31T23:59:59"),
    )

    assert selected == ("psl_day_model_19620101-19621231.nc",)


def test_open_concat_batch_dataset_normalizes_and_fixes_one_realization(
    monkeypatch, tmp_path
):
    calls = []
    normalized = xr.Dataset(
        {"psl": ("time", [1.0])},
        coords={"time": [np.datetime64("1962-01-01")]},
    )
    normalized.set_close(lambda: calls.append(("closed", "dataset.id")))

    class FakeProvider:
        def prepare(self, dataset, *, context=None):
            calls.append(
                ("prepare", context.dataset_id, context.operation, context.phase)
            )
            return dataset

        def apply(self, dataset, *, context=None):
            calls.append(
                (
                    "apply",
                    context.dataset_id,
                    context.operation,
                    context.phase,
                    context.output_dir,
                )
            )
            return dataset

    def normalize(collection, prepare_dataset):
        calls.append(("normalize", collection))
        prepare_dataset(normalized)
        return {"dataset.id": normalized}

    monkeypatch.setattr(concat_mod.normalise, "normalise_file_groups", normalize)

    result = concat_mod.open_concat_batch_dataset(
        "dataset.id",
        (
            "psl_day_model_19610101-19611231.nc",
            "psl_day_model_19620101-19621231.nc",
            "psl_day_model_19630101-19631231.nc",
        ),
        TimeBatch("1962-01-01", "1962-12-31"),
        provider=FakeProvider(),
        output_dir=tmp_path.as_posix(),
    )

    assert calls[:3] == [
        ("normalize", {"dataset.id": ("psl_day_model_19620101-19621231.nc",)}),
        ("prepare", "dataset.id", "concat", "prepare"),
        ("apply", "dataset.id", "concat", "apply", tmp_path.as_posix()),
    ]
    result.close()
    assert calls[-1] == ("closed", "dataset.id")


def test_concat_planning_time_closes_metadata_datasets():
    closed = []
    paths = ("1961.nc", "1962.nc")

    def opener(path):
        year = int(path[:4])
        dataset = xr.Dataset(
            coords={"time": [np.datetime64(f"{year}-01-01")]},
        )
        dataset.set_close(lambda: closed.append(path))
        return dataset

    time = concat_mod.concat_planning_time(
        {"dataset.id": paths},
        prepare_dataset=lambda dataset: dataset,
        opener=opener,
    )

    assert time.dt.year.values.tolist() == [1961, 1962]
    assert closed == list(paths)


def test_concat_realization_bytes_per_timestep_ignores_static_variables():
    closed = []
    dataset = xr.Dataset(
        {
            "tas": (
                ("time", "lat", "lon"),
                np.zeros((2, 3, 4), dtype="float32"),
            ),
            "lat_bnds": (
                ("lat", "bnds"),
                np.zeros((3, 2), dtype="float64"),
            ),
        },
        coords={"time": range(2)},
    )
    dataset.set_close(lambda: closed.append("input.nc"))

    bytes_per_timestep = concat_mod.concat_realization_bytes_per_timestep(
        {"dataset.id": ("input.nc",)},
        prepare_dataset=lambda opened: opened,
        opener=lambda _path: dataset,
    )

    assert bytes_per_timestep == 56
    assert closed == ["input.nc"]


def test_combined_concat_bytes_per_timestep_counts_all_ten_realizations():
    assert concat_mod.combined_concat_bytes_per_timestep(1_000_000, 10) == 10_000_000


def test_concat_reuses_configured_fix_provider(monkeypatch, tmp_path):
    calls = []
    source = DatasetSource("dataset.id", ["input.nc"])
    time = xr.date_range("2000-01-01", periods=2, freq="D", use_cftime=True)
    combined = xr.Dataset({"tas": ("time", [1.0, 2.0])}, coords={"time": time})
    final = ["https://example.com/fixed.nc"]

    class FakeProvider:
        def prepare(self, ds, *, context=None):
            calls.append(("prepare", ds, context.operation, context.phase))
            return ds

    fake_provider = FakeProvider()

    monkeypatch.setattr(
        concat_mod,
        "dataset_paths_by_id",
        lambda _collection: {"dataset.id": source.paths},
    )
    monkeypatch.setattr(
        concat_mod,
        "get_dataset_fix_provider",
        lambda: calls.append(("provider",)) or fake_provider,
    )
    monkeypatch.setattr(
        concat_mod,
        "concat_planning_time",
        lambda collection, prepare_dataset: calls.append(("planning", collection))
        or prepare_dataset(combined).time,
    )
    monkeypatch.setattr(
        concat_mod,
        "concat_realization_bytes_per_timestep",
        lambda collection, prepare_dataset: 16,
    )
    monkeypatch.setattr(
        concat_mod,
        "open_concat_batch_dataset",
        lambda dataset_id, paths, batch, provider, output_dir: calls.append(
            ("open", dataset_id, paths, batch.interval, provider, output_dir)
        )
        or combined.copy(deep=False),
    )
    monkeypatch.setattr(
        concat_mod,
        "prepare_concat_dataset",
        lambda dataset, dim, standard_name: combined,
    )
    monkeypatch.setattr(
        concat_mod,
        "finalise_concat_output",
        lambda ds, params, dim: final,
    )
    monkeypatch.setattr(
        concat_mod.config,
        "get_concat_batch_output_config",
        lambda: {
            "merge_outputs": True,
            "merge_target_bytes": 2_000_000_000,
            "max_output_bytes": 2_000_000_000,
        },
    )

    def merge(outputs, **options):
        calls.append(("merge", list(outputs), options))
        return list(outputs)

    monkeypatch.setattr(concat_mod, "merge_batch_outputs", merge)

    result = concat_mod.concat(
        collection=[source],
        dims=["realization"],
        output_dir=tmp_path.as_posix(),
    )

    assert result.file_uris == ["https://example.com/fixed.nc"]
    assert calls == [
        ("provider",),
        ("planning", {"dataset.id": ("input.nc",)}),
        ("prepare", combined, "concat", "prepare"),
        (
            "open",
            "dataset.id",
            ("input.nc",),
            "2000-01-01T00:00:00/2000-01-02T00:00:00",
            fake_provider,
            tmp_path.as_posix(),
        ),
        (
            "merge",
            final,
            {
                "file_namer": "standard",
                "output_type": "netcdf",
                "merge_outputs": True,
                "merge_target_bytes": 2_000_000_000,
                "max_output_bytes": 2_000_000_000,
            },
        ),
    ]


def test_concat_uses_synthetic_decadal_files_with_woodpecker_provider(
    monkeypatch, tmp_path, synthetic_cmip6_decadal_source
):
    monkeypatch.setattr("rook.fixes.providers.get_fix_backend", lambda: "woodpecker")

    result = concat_mod.concat(
        collection=[synthetic_cmip6_decadal_source],
        dims=["realization"],
        output_dir=tmp_path.as_posix(),
    )

    assert len(result.file_uris) == 1
    assert result.file_uris[0].startswith(tmp_path.as_posix())

    with xr.open_dataset(result.file_uris[0]) as dataset:
        assert dataset.sizes["time"] == 2
        assert dataset.sizes["realization"] == 1
        assert dataset.realization.attrs == {"standard_name": "realization"}
        assert dataset.attrs["project_id"] == "CMIP6"
        assert dataset.attrs["dataset_id"].startswith("CMIP6.DCPP.")


def test_finalise_concat_output_writes_to_configured_output_dir(tmp_path):
    dataset = xr.Dataset(
        {"tas": (("realization", "time"), [[280.0, 281.0]])},
        coords={
            "realization": [0],
            "time": np.array(["2000-01-01", "2000-02-01"], dtype="datetime64[ns]"),
        },
    )
    dataset.realization.attrs = {"standard_name": "realization"}

    outputs = concat_mod.finalise_concat_output(
        dataset,
        {
            "output_dir": tmp_path.as_posix(),
            "output_type": "netcdf",
            "split_method": "time:auto",
            "file_namer": "standard",
        },
        dim="realization",
    )

    assert len(outputs) == 1
    assert outputs[0].startswith(tmp_path.as_posix())
    assert (tmp_path / "output_001.nc").is_file()


def test_concat_dataset_selector_uses_lazy_low_level_component_subset():
    dask_array = __import__("dask.array", fromlist=["array"])
    time = xr.date_range("1962-01-01", "1962-12-31", freq="D", use_cftime=True)
    dataset = xr.Dataset(
        {"tas": ("time", dask_array.arange(len(time), chunks=31))},
        coords={"time": time},
    )
    parameter = concat_mod.time_components_parameter.TimeComponentsParameter(
        "month:aug|year:1962"
    )

    selector = concat_mod.concat_dataset_selector(parameter)
    selected = selector(dataset)

    assert selected.sizes["time"] == 31
    assert set(selected.time.dt.month.values) == {8}
    assert hasattr(selected.tas.data, "dask")


def test_parsed_time_components_are_plain_lists_for_low_level_clisops():
    parameter = concat_mod.time_components_parameter.TimeComponentsParameter(
        "month:aug|year:1962"
    )

    assert concat_mod.parsed_time_components(parameter) == {
        "year": [1962],
        "month": [8],
    }


def test_parsed_area_uses_clisops_bbox_bounds():
    parameter = concat_mod.area_parameter.AreaParameter("-10,30,30,70")

    assert concat_mod.parsed_area(parameter) == {
        "lon_bnds": (-10.0, 30.0),
        "lat_bnds": (30.0, 70.0),
    }


def test_concat_selector_combines_requested_time_and_components_lazily():
    dask_array = __import__("dask.array", fromlist=["array"])
    time = xr.date_range("1960-01-01", "1964-12-31", freq="D", use_cftime=True)
    lat = np.arange(20.0, 81.0, 10.0)
    lon = np.arange(0.0, 360.0, 10.0)
    values = dask_array.arange(len(time) * len(lat) * len(lon)).reshape(
        (len(time), len(lat), len(lon))
    )
    dataset = xr.Dataset(
        {"psl": (("time", "lat", "lon"), values.rechunk((365, 7, 36)))},
        coords={"time": time, "lat": lat, "lon": lon},
    )
    dataset.lat.attrs = {"standard_name": "latitude", "units": "degrees_north"}
    dataset.lon.attrs = {"standard_name": "longitude", "units": "degrees_east"}
    requested_time = concat_mod.time_parameter.TimeParameter("1962/1962")
    components = concat_mod.time_components_parameter.TimeComponentsParameter(
        "month:aug|year:1962"
    )

    selected = concat_mod.concat_dataset_selector(
        components,
        requested_time=requested_time,
        area="-10,30,35,70",
    )(dataset)

    assert selected.sizes["time"] == 31
    assert set(selected.time.dt.year.values) == {1962}
    assert set(selected.time.dt.month.values) == {8}
    assert selected.sizes["lat"] == 5
    assert selected.sizes["lon"] == 5
    assert selected.lon.values.tolist() == [-10.0, 0.0, 10.0, 20.0, 30.0]
    assert isinstance(selected.psl.data, dask_array.Array)


def test_area_pushdown_reduces_realizations_before_concat_and_is_equivalent(
    monkeypatch,
):
    dask_array = __import__("dask.array", fromlist=["array"])
    time = xr.date_range("1962-01-01", "1962-12-31", freq="D", use_cftime=True)
    lat = np.arange(20.0, 81.0, 10.0)
    lon = np.arange(0.0, 360.0, 10.0)
    datasets = []
    for realization in range(2):
        values = dask_array.arange(len(time) * len(lat) * len(lon)).reshape(
            (len(time), len(lat), len(lon))
        )
        datasets.append(
            xr.Dataset(
                {
                    "psl": (
                        ("time", "lat", "lon"),
                        values.rechunk((365, 7, 36)) + realization,
                    )
                },
                coords={"time": time, "lat": lat, "lon": lon},
            )
        )
        datasets[-1].lat.attrs = {
            "standard_name": "latitude",
            "units": "degrees_north",
        }
        datasets[-1].lon.attrs = {
            "standard_name": "longitude",
            "units": "degrees_east",
        }

    original_concat = xr.concat
    expected = concat_mod.subset(
        original_concat(datasets, dim="realization"),
        area="-10,30,35,70",
        output_type="xarray",
    )[0]
    seen_by_concat = []

    def record_concat(selected, dim):
        seen_by_concat.append(
            [(dataset.sizes["lat"], dataset.sizes["lon"]) for dataset in selected]
        )
        return original_concat(selected, dim=dim)

    monkeypatch.setattr("rook.batch.concat.xr.concat", record_concat)
    processor = ConcatBatch(
        ConcatBatchPlanner(
            target_timesteps=365,
            min_batch_years=1,
            max_batch_years=1,
        )
    )
    collection, open_dataset = _concat_batch_inputs(datasets)

    outputs = processor.process(
        collection,
        planning_time=xr.DataArray(time, dims="time"),
        dim="realization",
        open_dataset=open_dataset,
        operation=lambda combined, _time, _index, _total: [
            xr.testing.assert_equal(combined, expected)
        ],
        select_dataset=concat_mod.concat_dataset_selector(
            None,
            area="-10,30,35,70",
        ),
    )

    assert outputs == [None]
    assert seen_by_concat == [[(5, 5), (5, 5)]]


def test_area_pushdown_accepts_dataset_longitude_convention():
    lon = np.arange(0.0, 360.0, 10.0)
    lat = np.arange(20.0, 81.0, 10.0)
    dataset = xr.Dataset(
        {"psl": (("lat", "lon"), np.zeros((len(lat), len(lon))))},
        coords={"lat": lat, "lon": lon},
    )
    dataset.lat.attrs = {"standard_name": "latitude", "units": "degrees_north"}
    dataset.lon.attrs = {"standard_name": "longitude", "units": "degrees_east"}

    selected = concat_mod.concat_dataset_selector(
        None,
        area="10,30,35,70",
    )(dataset)

    assert selected.lon.values.tolist() == [10.0, 20.0, 30.0]
    assert selected.lat.values.tolist() == [30.0, 40.0, 50.0, 60.0, 70.0]


def test_concat_batch_sees_only_requested_component_days(monkeypatch):
    time = xr.date_range("1960-01-01", "1964-12-31", freq="D", use_cftime=True)
    datasets = [
        xr.Dataset({"psl": ("time", range(len(time)))}, coords={"time": time})
        for _ in range(2)
    ]
    requested_time = concat_mod.time_parameter.TimeParameter("1962/1962")
    components = concat_mod.time_components_parameter.TimeComponentsParameter(
        "month:aug|year:1962"
    )
    seen_by_concat = []
    original_concat = xr.concat

    def record_concat(selected, dim):
        seen_by_concat.append([dataset.sizes["time"] for dataset in selected])
        return original_concat(selected, dim=dim)

    monkeypatch.setattr("rook.batch.concat.xr.concat", record_concat)
    processor = ConcatBatch(
        ConcatBatchPlanner(
            target_timesteps=1826,
            min_batch_years=1,
            max_batch_years=5,
        )
    )
    collection, open_dataset = _concat_batch_inputs(datasets)

    outputs = processor.process(
        collection,
        planning_time=xr.DataArray(time, dims="time"),
        dim="realization",
        open_dataset=open_dataset,
        operation=lambda combined, _time, _index, _total: [combined.sizes["time"]],
        requested_time=concat_mod.effective_concat_time(requested_time, components),
        select_dataset=concat_mod.concat_dataset_selector(
            components,
            requested_time=requested_time,
        ),
        include_batch=concat_mod.concat_batch_filter(components),
    )

    assert outputs == [31]
    assert seen_by_concat == [[31, 31]]


def test_concat_planner_uses_effective_requested_interval():
    time = xr.date_range("1955-01-01", "1969-12-31", freq="D", use_cftime=True)
    dataset = xr.Dataset(coords={"time": time})
    requested_time = concat_mod.time_parameter.TimeParameter("1962/1962")
    components = concat_mod.time_components_parameter.TimeComponentsParameter(
        "month:aug|year:1962"
    )

    batches = ConcatBatchPlanner(
        target_timesteps=1826,
        min_batch_years=1,
        max_batch_years=5,
    ).plan(
        dataset.time,
        concat_mod.effective_concat_time(requested_time, components),
    )

    assert batches == [TimeBatch("1962-01-01T00:00:00", "1962-12-31T23:59:59")]


def test_concat_temporal_plan_excludes_unrequested_component_years(capsys):
    components = concat_mod.time_components_parameter.TimeComponentsParameter(
        "month:aug|year:1961,1963"
    )

    effective_time = concat_mod.effective_concat_time(None, components)
    include_batch = concat_mod.concat_batch_filter(components)

    assert effective_time.get_bounds() == (
        "1961-01-01T00:00:00",
        "1963-12-31T23:59:59",
    )
    assert include_batch(TimeBatch("1961-01-01", "1961-12-31")) is True
    assert include_batch(TimeBatch("1962-01-01", "1962-12-31")) is False
    assert include_batch(TimeBatch("1963-01-01", "1963-12-31")) is True
    diagnostics = capsys.readouterr().err
    assert "component_years=[1961, 1963]" in diagnostics
    assert "effective=('1961-01-01T00:00:00', '1963-12-31T23:59:59')" in diagnostics


def test_concat_selector_without_components_preserves_requested_time_behavior():
    time = xr.date_range("1960-01-01", "1964-12-31", freq="D", use_cftime=True)
    dataset = xr.Dataset(
        {"psl": (("time", "lat", "lon"), np.zeros((len(time), 2, 3)))},
        coords={"time": time, "lat": [40.0, 50.0], "lon": [0.0, 10.0, 20.0]},
    )

    selected = concat_mod.concat_dataset_selector(
        None,
        requested_time=concat_mod.time_parameter.TimeParameter("1962/1962"),
    )(dataset)

    assert selected.sizes["time"] == 365
    assert set(selected.time.dt.year.values) == {1962}
    assert selected.sizes["lat"] == 2
    assert selected.sizes["lon"] == 3


def test_concat_dataset_selector_is_disabled_without_time_components():
    parameter = concat_mod.time_components_parameter.TimeComponentsParameter(None)

    assert concat_mod.concat_dataset_selector(parameter) is None


def test_prepare_concat_dataset_sets_realization_coordinate_metadata():
    datasets = [
        xr.Dataset(
            {
                "tas": ("time", [1]),
                "time_bnds": (("time", "bnds"), [[0, 1]]),
            },
            coords={"time": [0]},
        ),
        xr.Dataset(
            {
                "tas": ("time", [2]),
                "time_bnds": (("time", "bnds"), [[0, 1]]),
            },
            coords={"time": [0]},
        ),
    ]

    result = concat_mod.prepare_concat_dataset(
        xr.concat(datasets, dim="realization"),
        dim="realization",
        standard_name="realization",
    )

    assert result.realization.dtype == "int32"
    assert result.realization.attrs == {"standard_name": "realization"}
    assert "time_bnds" not in result.variables


def test_concat_batches_lazy_realization_slices_and_finishes_writes_sequentially(
    monkeypatch, tmp_path
):
    dask_array = __import__("dask.array", fromlist=["array"])
    time = xr.date_range("2000-01-01", periods=24, freq="MS", use_cftime=True)
    datasets = [
        xr.Dataset(
            {"tas": ("time", dask_array.arange(24, chunks=6) + realization)},
            coords={"time": time},
        )
        for realization in range(2)
    ]
    sources = {
        "first.id": ("first.nc",),
        "second.id": ("second.nc",),
    }
    events = []
    prepared = object()

    class MaterializedBatch:
        def __init__(self, index):
            self.index = index

        def close(self):
            events.append(("closed", self.index))

    monkeypatch.setattr(concat_mod, "dataset_paths_by_id", lambda _collection: sources)
    monkeypatch.setattr(concat_mod, "get_dataset_fix_provider", lambda: prepared)
    monkeypatch.setattr(
        concat_mod,
        "concat_planning_time",
        lambda _collection, prepare_dataset: xr.DataArray(time, dims="time"),
    )
    monkeypatch.setattr(
        concat_mod,
        "concat_realization_bytes_per_timestep",
        lambda _collection, prepare_dataset: 16,
    )

    opened = 0

    def open_batch(dataset_id, paths, batch, provider, output_dir):
        nonlocal opened
        realization = list(sources).index(dataset_id)
        dataset = datasets[realization].copy(deep=False)
        opened += 1
        identity = (batch.start[:4], dataset_id, opened)
        events.append(("opened", *identity))
        dataset.set_close(lambda: events.append(("source-closed", *identity)))
        assert paths == sources[dataset_id]
        assert provider is prepared
        assert output_dir == tmp_path.as_posix()
        return dataset

    monkeypatch.setattr(
        concat_mod,
        "open_concat_batch_dataset",
        open_batch,
    )
    monkeypatch.setattr(
        concat_mod.config,
        "get_concat_batching_config",
        lambda: {
            "target_timesteps": 12,
            "min_batch_years": 1,
            "max_batch_years": 1,
        },
    )

    def combine(selected, dim):
        index = len([event for event in events if event[0] == "combined"]) + 1
        if index > 1:
            assert any(
                event[:3] == ("source-closed", "2000", "second.id") for event in events
            )
        assert dim == "realization"
        assert [dataset.sizes["time"] for dataset in selected] == [12, 12]
        assert all(hasattr(dataset.tas.data, "dask") for dataset in selected)
        events.append(("combined", index))
        return MaterializedBatch(index)

    def finalise(_dataset, params, dim):
        index = len([event for event in events if event[0] == "written"]) + 1
        events.append(("written", index, params["time"].get_bounds(), dim))
        return [str(tmp_path / f"concat-{index}.nc")]

    monkeypatch.setattr("rook.batch.concat.xr.concat", combine)
    monkeypatch.setattr(
        concat_mod,
        "prepare_concat_dataset",
        lambda dataset, dim, standard_name: dataset,
    )
    monkeypatch.setattr(concat_mod, "finalise_concat_output", finalise)

    result = concat_mod.concat(
        collection=[DatasetSource("dataset.id", ["input.nc"])],
        dims=["realization"],
        output_dir=tmp_path.as_posix(),
    )

    assert next(iter(result._results.values())) == [
        str(tmp_path / "concat-1.nc"),
        str(tmp_path / "concat-2.nc"),
    ]
    assert [event[0] for event in events].count("opened") == 4
    assert [event[0] for event in events].count("source-closed") == 4
    assert [event[0] for event in events].count("combined") == 2
    assert [event[0] for event in events].count("written") == 2
    assert [event[0] for event in events].count("closed") == 2
