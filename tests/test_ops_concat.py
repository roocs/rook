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


def test_apply_concat_calendar_fix_applies_decadal_calendar_fix(monkeypatch):
    calls = []
    source = xr.Dataset(attrs={"source": "input"})

    class FakeProvider:
        def prepare(self, ds, *, context=None):
            calls.append((ds.attrs["source"], context.operation, context.phase))
            return ds

    result = concat_mod.apply_concat_calendar_fix(source, FakeProvider())

    assert result is source
    assert calls == [("input", "concat", "prepare")]


def test_apply_concat_dataset_fixes_preserves_dataset_identity(monkeypatch, tmp_path):
    calls = []
    first = xr.Dataset(attrs={"source": "first"})
    second = xr.Dataset(attrs={"source": "second"})

    class FakeProvider:
        def apply(self, ds, *, context=None):
            calls.append((context.dataset_id, ds.attrs["source"], context.output_dir))
            return ds.assign_attrs(fixed=context.dataset_id)

    monkeypatch.setattr(
        concat_mod, "get_dataset_fix_provider", lambda fix_backend: FakeProvider()
    )

    datasets = concat_mod.apply_concat_dataset_fixes(
        {"first.id": first, "second.id": second},
        output_dir=tmp_path.as_posix(),
    )

    assert calls == [
        ("first.id", "first", tmp_path.as_posix()),
        ("second.id", "second", tmp_path.as_posix()),
    ]
    assert [ds.attrs["fixed"] for ds in datasets] == ["first.id", "second.id"]


def test_apply_concat_dataset_fixes_can_use_woodpecker_backend(monkeypatch, tmp_path):
    calls = []
    source = xr.Dataset(attrs={"source": "first"})

    class FakeProvider:
        def apply(self, ds, *, context=None):
            calls.append(
                (
                    context.dataset_id,
                    ds.attrs["source"],
                    context.output_dir,
                    context.recipe_id,
                )
            )
            return ds.assign_attrs(fixed_with="woodpecker")

    monkeypatch.setattr(
        concat_mod,
        "get_dataset_fix_provider",
        lambda fix_backend: calls.append(("provider", fix_backend)) or FakeProvider(),
    )

    datasets = concat_mod.apply_concat_dataset_fixes(
        {"first.id": source},
        output_dir=tmp_path.as_posix(),
        fix_backend="woodpecker",
    )

    assert calls == [
        ("provider", "woodpecker"),
        (
            "first.id",
            "first",
            tmp_path.as_posix(),
            concat_mod.WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
        ),
    ]
    assert datasets[0].attrs["fixed_with"] == "woodpecker"


def test_concat_passes_fix_backend_to_dataset_fixes(monkeypatch, tmp_path):
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
        lambda fix_backend: calls.append(("provider", fix_backend)) or fake_provider,
    )
    monkeypatch.setattr(
        concat_mod.normalise,
        "normalise_file_groups",
        lambda collection, prepare_dataset: {"dataset.id": prepare_dataset(source)},
    )
    monkeypatch.setattr(
        concat_mod,
        "apply_concat_dataset_fixes",
        lambda collection, output_dir, fix_backend="legacy", fix_provider=None: calls.append(
            (collection, output_dir, fix_backend, fix_provider)
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
        fix_backend="woodpecker",
    )

    assert result.file_uris == ["https://example.com/fixed.nc"]
    assert calls == [
        ("provider", "woodpecker"),
        ("prepare", source, "concat", "prepare"),
        (
            {"dataset.id": source},
            tmp_path.as_posix(),
            "woodpecker",
            fake_provider,
        ),
    ]


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
