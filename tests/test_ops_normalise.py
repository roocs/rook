import xarray as xr

from rook.operations import normalise


def test_normalise_file_groups_opens_prepares_and_concatenates_files():
    calls = []

    def fake_open(path):
        calls.append(("open", path))
        return xr.Dataset({"tas": ("time", [1])}, coords={"time": [path]})

    def prepare(ds):
        calls.append(("prepare", ds.time.values[0]))
        return ds

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


def test_normalise_file_groups_allows_plain_opening_without_prepare():
    collection = normalise.normalise_file_groups(
        {"dataset": ("one",)},
        opener=lambda path: xr.Dataset(
            {"tas": ("time", [1])},
            coords={"time": [path]},
        ),
    )

    assert collection["dataset"].time.values.tolist() == ["one"]
