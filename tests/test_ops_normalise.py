import xarray as xr

from rook.diagnostics import dataset_summary
from rook.operations import normalise


def test_lazy_group_opener_uses_storage_chunks_without_auto_rechunking(
    monkeypatch, tmp_path
):
    calls = []
    expected = object()

    def fake_open(path, **kwargs):
        calls.append((path, kwargs))
        return expected

    monkeypatch.setattr(normalise, "open_xr_dataset", fake_open)

    result = normalise.open_lazy_xr_dataset(tmp_path / "part.nc")

    assert result is expected
    assert calls == [(str(tmp_path / "part.nc"), {"chunks": {}})]


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


def test_normalized_group_close_closes_every_opened_file_dataset():
    closed = []

    def opener(path):
        dataset = xr.Dataset({"tas": ("time", [1])}, coords={"time": [path]})
        dataset.set_close(lambda: closed.append(path))
        return dataset

    normalized = normalise.normalise_file_groups(
        {"dataset": ("one", "two")},
        opener=opener,
    )["dataset"]

    assert closed == []
    normalized.close()
    assert closed == ["one", "two"]


def test_dataset_summary_reports_backing_type_and_compact_chunks():
    dask_array = __import__("dask.array", fromlist=["array"])
    dataset = xr.Dataset(
        {
            "lazy": ("time", dask_array.arange(12, chunks=4)),
            "eager": ("time", list(range(12))),
        }
    )

    summary = dataset_summary(dataset)

    assert "sizes={'time': 12}" in summary
    assert "lazy[dask:Array;chunks=time:3x4]" in summary
    assert "eager[numpy:ndarray;chunks=none]" in summary


def test_normalise_file_groups_keeps_grouped_netcdf_data_dask_backed(tmp_path, capsys):
    dask_array = __import__("dask.array", fromlist=["Array"])
    paths = []
    for index, times in enumerate(([0, 1], [2, 3]), start=1):
        path = tmp_path / f"part-{index}.nc"
        xr.Dataset(
            {"psl": (("time", "lat"), [[index] * 3, [index + 1] * 3])},
            coords={"time": times, "lat": [10.0, 20.0, 30.0]},
        ).to_netcdf(
            path,
            engine="h5netcdf",
            encoding={"psl": {"chunksizes": (1, 3)}},
        )
        paths.append(path)

    opened_backings = []

    def record_backing(dataset):
        opened_backings.append(type(dataset.psl.data))
        return dataset

    collection = normalise.normalise_file_groups(
        {"realization": paths},
        prepare_dataset=record_backing,
    )
    dataset = collection["realization"]

    assert opened_backings == [dask_array.Array, dask_array.Array]
    assert isinstance(dataset.psl.data, dask_array.Array)
    assert dataset.sizes == {"time": 4, "lat": 3}
    assert dataset.psl.compute().values.tolist() == [
        [1, 1, 1],
        [2, 2, 2],
        [2, 2, 2],
        [3, 3, 3],
    ]
    diagnostics = capsys.readouterr().err.splitlines()
    assert any(
        "after opening file" in line and "psl[dask:Array" in line
        for line in diagnostics
    )
    assert any(
        "after normalise xr.concat" in line and "psl[dask:Array" in line
        for line in diagnostics
    )
    dataset.close()
