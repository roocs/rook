import numpy as np
import xarray as xr

import rook.operations.concat as concat_mod
from rook.io.datasets import DatasetSource


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
            calls.append((ds.attrs["source"], context.operation, context.phase))
            return ds

    result = concat_mod.apply_concat_calendar_fix(source, FakeProvider())

    assert result is source
    assert calls == [("input", "concat", "prepare")]


def test_apply_concat_dataset_fixes_preserves_dataset_identity(tmp_path):
    calls = []
    first = xr.Dataset(attrs={"source": "first"})
    second = xr.Dataset(attrs={"source": "second"})

    class FakeProvider:
        def apply(self, ds, *, context=None):
            calls.append((context.dataset_id, ds.attrs["source"], context.output_dir))
            return ds.assign_attrs(fixed=context.dataset_id)

    datasets = concat_mod.apply_concat_dataset_fixes(
        {"first.id": first, "second.id": second},
        output_dir=tmp_path.as_posix(),
        provider=FakeProvider(),
    )

    assert calls == [
        ("first.id", "first", tmp_path.as_posix()),
        ("second.id", "second", tmp_path.as_posix()),
    ]
    assert [ds.attrs["fixed"] for ds in datasets] == ["first.id", "second.id"]


def test_concat_reuses_configured_fix_provider(monkeypatch, tmp_path):
    calls = []
    source = DatasetSource("dataset.id", ["input.nc"])
    combined = xr.Dataset({"tas": ("realization", [1.0])})
    final = ["https://example.com/fixed.nc"]

    class FakeProvider:
        def prepare(self, ds, *, context=None):
            calls.append(("prepare", ds, context.operation, context.phase))
            return ds

    fake_provider = FakeProvider()

    monkeypatch.setattr(
        concat_mod, "dataset_paths_by_id", lambda collection: collection
    )
    monkeypatch.setattr(
        concat_mod,
        "get_dataset_fix_provider",
        lambda: calls.append(("provider",)) or fake_provider,
    )
    monkeypatch.setattr(
        concat_mod.normalise,
        "normalise_file_groups",
        lambda collection, prepare_dataset: {"dataset.id": prepare_dataset(source)},
    )
    monkeypatch.setattr(
        concat_mod,
        "apply_concat_dataset_fixes",
        lambda collection, output_dir, provider: calls.append(
            (collection, output_dir, provider)
        )
        or [combined],
    )
    monkeypatch.setattr(
        concat_mod,
        "combine_concat_datasets",
        lambda datasets, dim, standard_name: combined,
    )
    monkeypatch.setattr(
        concat_mod,
        "finalise_concat_output",
        lambda ds, params, dim: final,
    )

    result = concat_mod.concat(
        collection=[source],
        dims=["realization"],
        output_dir=tmp_path.as_posix(),
    )

    assert result.file_uris == ["https://example.com/fixed.nc"]
    assert calls == [
        ("provider",),
        ("prepare", source, "concat", "prepare"),
        (
            {"dataset.id": source},
            tmp_path.as_posix(),
            fake_provider,
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


def test_combine_concat_datasets_sets_realization_coordinate_metadata():
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

    result = concat_mod.combine_concat_datasets(
        datasets,
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
    source = DatasetSource("dataset.id", ["input.nc"])
    events = []
    prepared = object()

    class MaterializedBatch:
        def __init__(self, index):
            self.index = index

        def close(self):
            events.append(("closed", self.index))

    monkeypatch.setattr(
        concat_mod, "dataset_paths_by_id", lambda _collection: {"dataset.id": source}
    )
    monkeypatch.setattr(concat_mod, "get_dataset_fix_provider", lambda: prepared)
    monkeypatch.setattr(
        concat_mod.normalise,
        "normalise_file_groups",
        lambda _collection, prepare_dataset: events.append(("normalised",))
        or {"dataset.id": source},
    )
    monkeypatch.setattr(
        concat_mod,
        "apply_concat_dataset_fixes",
        lambda _collection, output_dir, provider: events.append(
            ("fixed", output_dir, provider)
        )
        or datasets,
    )
    monkeypatch.setattr(
        concat_mod.config,
        "get_batching_config",
        lambda: {
            "target_timesteps": 12,
            "min_batch_years": 1,
            "max_batch_years": 1,
        },
    )

    def combine(selected, dim, standard_name):
        index = len([event for event in events if event[0] == "combined"]) + 1
        if index > 1:
            assert events[-1] == ("closed", index - 1)
        assert dim == standard_name == "realization"
        assert [dataset.sizes["time"] for dataset in selected] == [12, 12]
        assert all(hasattr(dataset.tas.data, "dask") for dataset in selected)
        events.append(("combined", index))
        return MaterializedBatch(index)

    def finalise(_dataset, params, dim):
        index = len([event for event in events if event[0] == "written"]) + 1
        events.append(("written", index, params["time"].get_bounds(), dim))
        return [str(tmp_path / f"concat-{index}.nc")]

    monkeypatch.setattr(concat_mod, "combine_concat_datasets", combine)
    monkeypatch.setattr(concat_mod, "finalise_concat_output", finalise)

    result = concat_mod.concat(
        collection=[source],
        dims=["realization"],
        output_dir=tmp_path.as_posix(),
    )

    assert next(iter(result._results.values())) == [
        str(tmp_path / "concat-1.nc"),
        str(tmp_path / "concat-2.nc"),
    ]
    assert [event[0] for event in events] == [
        "normalised",
        "fixed",
        "combined",
        "written",
        "closed",
        "combined",
        "written",
        "closed",
    ]
