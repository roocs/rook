import xarray as xr

from rook.operations import normalise


def test_normalise_file_groups_opens_prepares_and_concatenates_files(monkeypatch):
    calls = []
    concat_calls = []
    original_concat = xr.concat

    def fake_open(path):
        calls.append(("open", path))
        return xr.Dataset({"tas": ("time", [1])}, coords={"time": [path]})

    def prepare(ds):
        calls.append(("prepare", ds.time.values[0]))
        return ds

    def concat(datasets, **kwargs):
        concat_calls.append((datasets, kwargs))
        return original_concat(datasets, **kwargs)

    monkeypatch.setattr(normalise.xr, "concat", concat)

    collection = normalise.normalise_file_groups(
        {"dataset": ("one", "two")},
        opener=fake_open,
        prepare_dataset=prepare,
    )

    assert calls == [
        ("open", "one"),
        ("prepare", "one"),
        ("open", "two"),
        ("prepare", "two"),
    ]
    assert list(collection) == ["dataset"]
    assert collection["dataset"].sizes["time"] == 2
    assert len(concat_calls) == 1
    assert concat_calls[0][1] == {
        "dim": "time",
        "data_vars": "minimal",
        "coords": "minimal",
        "compat": "override",
        "join": "exact",
    }


def test_normalise_file_groups_allows_plain_opening_without_prepare():
    collection = normalise.normalise_file_groups(
        {"first": ("one",), "second": ("two",)},
        opener=lambda path: xr.Dataset(
            {"tas": ("time", [1])},
            coords={"time": [path]},
        ),
    )

    assert list(collection) == ["first", "second"]
    assert collection["first"].time.values.tolist() == ["one"]
    assert collection["second"].time.values.tolist() == ["two"]


def test_dataset_summary_reports_backing_type_and_compact_chunks():
    dask_array = __import__("dask.array", fromlist=["array"])
    dataset = xr.Dataset(
        {
            "lazy": ("time", dask_array.arange(12, chunks=4)),
            "eager": ("time", list(range(12))),
        }
    )

    summary = normalise._dataset_summary(dataset)

    assert "sizes={'time': 12}" in summary
    assert "lazy[dask:Array;chunks=time:3x4]" in summary
    assert "eager[numpy:ndarray;chunks=none]" in summary
