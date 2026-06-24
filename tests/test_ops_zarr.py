import xarray as xr

from rook.utils.ops.subset import subset


def test_subset_local_zarr_store(tmp_path):
    store = tmp_path / "input.zarr"
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()

    dataset = xr.Dataset(
        {
            "tas": (
                ("time", "lat", "lon"),
                [
                    [[280.0, 281.0], [282.0, 283.0]],
                    [[284.0, 285.0], [286.0, 287.0]],
                    [[288.0, 289.0], [290.0, 291.0]],
                ],
            )
        },
        coords={
            "time": xr.date_range("2000-01-01", periods=3),
            "lat": [-10.0, 10.0],
            "lon": [0.0, 20.0],
        },
    )
    dataset["time"].attrs["standard_name"] = "time"
    dataset["lat"].attrs["standard_name"] = "latitude"
    dataset["lon"].attrs["standard_name"] = "longitude"
    dataset.to_zarr(store, mode="w")

    result = subset(
        collection=str(store),
        output_dir=output_dir,
    )

    assert len(result.file_uris) == 1
    with xr.open_dataset(result.file_uris[0]) as output:
        assert output.sizes["time"] == 3
        assert output["tas"].shape == (3, 2, 2)
