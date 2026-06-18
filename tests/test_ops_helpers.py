from dataclasses import FrozenInstanceError

import pytest
import xarray as xr

from rook import config
import rook.io.datasets as helpers


def source(dataset_id, paths):
    return helpers.DatasetSource(dataset_id=dataset_id, paths=paths)


def test_dataset_source_normalizes_scalar_and_list_paths():
    assert source(None, "one.nc").paths == ("one.nc",)
    assert source("project.dataset", ["one.nc", "two.nc"]).paths == (
        "one.nc",
        "two.nc",
    )


def test_dataset_source_is_immutable():
    dataset_source = source(None, "one.nc")

    with pytest.raises(FrozenInstanceError):
        dataset_source.paths = ("two.nc",)


def test_dataset_source_rejects_multiple_zarr_or_kerchunk_paths():
    with pytest.raises(ValueError, match="exactly one path"):
        source(None, ["one.zarr", "two.zarr"])

    with pytest.raises(ValueError, match="exactly one path"):
        source(None, ["one.json", "two.json"])


def test_open_dataset_applies_fixes(monkeypatch):
    calls = {"open": 0, "fix": 0}

    def fake_open(file_paths):
        calls["open"] += 1
        assert file_paths == ["a.nc"]
        return "DATASET"

    def fake_apply(ds_id, ds):
        calls["fix"] += 1
        assert ds_id == "project.dataset"
        assert ds == "DATASET"
        return "FIXED"

    monkeypatch.setattr(helpers, "open_xr_dataset", fake_open)
    monkeypatch.setattr(helpers, "apply_dataset_fixes", fake_apply)
    monkeypatch.setattr(helpers, "is_kerchunk_file", lambda _: False)

    result = helpers.open_dataset(
        source("project.dataset", ["a.nc"]), apply_fixes=True
    )

    assert result == "FIXED"
    assert calls == {"open": 1, "fix": 1}


def test_open_dataset_skips_fixes_when_disabled(monkeypatch):
    calls = {"open": 0, "fix": 0}

    def fake_open(file_paths):
        calls["open"] += 1
        return "DATASET"

    def fake_apply(ds_id, ds):
        calls["fix"] += 1
        return "FIXED"

    monkeypatch.setattr(helpers, "open_xr_dataset", fake_open)
    monkeypatch.setattr(helpers, "apply_dataset_fixes", fake_apply)
    monkeypatch.setattr(helpers, "is_kerchunk_file", lambda _: False)

    result = helpers.open_dataset(
        source("project.dataset", ["a.nc"]), apply_fixes=False
    )

    assert result == "DATASET"
    assert calls == {"open": 1, "fix": 0}


def test_open_dataset_skips_fixes_for_kerchunk(monkeypatch):
    calls = {"open": 0, "fix": 0}

    def fake_open(file_paths):
        calls["open"] += 1
        return "DATASET"

    def fake_apply(ds_id, ds):
        calls["fix"] += 1
        return "FIXED"

    monkeypatch.setattr(helpers, "open_xr_dataset", fake_open)
    monkeypatch.setattr(helpers, "apply_dataset_fixes", fake_apply)
    monkeypatch.setattr(helpers, "is_kerchunk_file", lambda _: True)

    result = helpers.open_dataset(
        source(None, ["kerchunk.json"]), apply_fixes=True
    )

    assert result == "DATASET"
    assert calls == {"open": 1, "fix": 0}


def test_open_dataset_skips_fixes_without_catalog_dataset_id(monkeypatch):
    monkeypatch.setattr(helpers, "open_xr_dataset", lambda _paths: "DATASET")

    def fail_apply_fixes(_ds_id, _ds):
        raise AssertionError("Direct paths must not trigger project fixes")

    monkeypatch.setattr(helpers, "apply_dataset_fixes", fail_apply_fixes)

    result = helpers.open_dataset(source(None, "direct.nc"), apply_fixes=True)

    assert result == "DATASET"


def test_is_kerchunk_file_local_json():
    assert helpers.is_kerchunk_file("kerchunk.json") is True


def test_is_kerchunk_file_url_with_query():
    assert (
        helpers.is_kerchunk_file(
            "https://example.org/path/catalog.parquet?token=abc123"
        )
        is True
    )


def test_is_kerchunk_file_reference_scheme():
    assert helpers.is_kerchunk_file("reference://") is True


def test_is_kerchunk_file_non_kerchunk_path():
    assert helpers.is_kerchunk_file("/data/file.nc") is False


def test_detect_format_netcdf():
    assert helpers.detect_format(source(None, "file.nc")) is helpers.DatasetFormat.NETCDF


def test_detect_format_kerchunk_url_with_query():
    dataset_source = source(None, "https://example.org/ref.json?token=abc")

    assert helpers.detect_format(dataset_source) is helpers.DatasetFormat.KERCHUNK


def test_is_zarr_store_local_path():
    assert helpers.is_zarr_store("/data/example.zarr") is True


def test_is_zarr_store_url_with_query_and_trailing_slash():
    assert helpers.is_zarr_store("s3://bucket/example.zarr/?token=abc") is True


def test_is_zarr_store_netcdf_path():
    assert helpers.is_zarr_store("s3://bucket/example.nc") is False


def test_detect_format_zarr_from_catalog_paths():
    assert helpers.detect_format(
        source("project.dataset", ["s3://bucket/example.zarr"])
    ) is helpers.DatasetFormat.ZARR


def test_detect_transport_is_independent_of_format():
    assert (
        helpers.detect_transport(source(None, "s3://bucket/file.nc"))
        is helpers.Transport.S3
    )
    assert (
        helpers.detect_transport(source(None, "s3://bucket/example.zarr"))
        is helpers.Transport.S3
    )
    assert (
        helpers.detect_transport(source(None, "https://example.org/ref.json"))
        is helpers.Transport.HTTP
    )


def test_detect_transport_rejects_mixed_transports():
    with pytest.raises(ValueError, match="mixed transports"):
        helpers.detect_transport(source(None, ["/data/one.nc", "s3://bucket/two.nc"]))


def test_open_dataset_opens_local_zarr_store(tmp_path):
    store = tmp_path / "example.zarr"
    expected = xr.Dataset({"tas": ("time", [280.0, 281.0])})
    expected.to_zarr(store, mode="w")

    result = helpers.open_dataset(source(None, str(store)), apply_fixes=False)

    xr.testing.assert_equal(result, expected)
    result.close()


def test_open_dataset_keeps_local_netcdf_path(tmp_path, monkeypatch):
    path = tmp_path / "example.nc"
    expected = xr.Dataset({"tas": ("time", [280.0, 281.0])})
    expected.to_netcdf(path)

    def fail_open_zarr(*_args, **_kwargs):
        raise AssertionError("NetCDF inputs must not use the Zarr opener")

    monkeypatch.setattr(helpers.xr, "open_zarr", fail_open_zarr)

    result = helpers.open_dataset(
        source("project.dataset", [str(path)]), apply_fixes=False
    )

    xr.testing.assert_equal(result, expected)
    result.close()


def test_open_dataset_passes_s3_options_to_zarr(monkeypatch):
    calls = {}

    def fake_open_zarr(store, **kwargs):
        calls["store"] = store
        calls["kwargs"] = kwargs
        return "DATASET"

    monkeypatch.setattr(helpers.xr, "open_zarr", fake_open_zarr)
    monkeypatch.setattr(
        config,
        "CONFIG",
        {"s3": {"anon": "true", "endpoint_url": "https://s3.example.org"}},
    )

    result = helpers.open_dataset(
        source(None, "s3://example-bucket/path/example.zarr"),
        apply_fixes=False,
    )

    assert result == "DATASET"
    assert calls == {
        "store": "s3://example-bucket/path/example.zarr",
        "kwargs": {
            "storage_options": {
                "anon": True,
                "client_kwargs": {"endpoint_url": "https://s3.example.org"},
            }
        },
    }


def test_open_dataset_skips_fixes_for_direct_zarr(monkeypatch):
    monkeypatch.setattr(helpers.xr, "open_zarr", lambda _store, **_kwargs: "DATASET")

    def fail_apply_fixes(_ds_id, _ds):
        raise AssertionError("Fix lookup should not be called for direct Zarr input")

    monkeypatch.setattr(helpers, "apply_dataset_fixes", fail_apply_fixes)

    result = helpers.open_dataset(
        source(None, "/data/example.zarr"), apply_fixes=True
    )

    assert result == "DATASET"


def test_get_storage_options_for_s3_source(monkeypatch):
    monkeypatch.setattr(
        config,
        "CONFIG",
        {"s3": {"anon": "true", "endpoint_url": "https://s3.example.org"}},
    )

    options = helpers.get_storage_options(source(None, "s3://bucket/file.nc"))

    assert options == {
        "anon": True,
        "client_kwargs": {"endpoint_url": "https://s3.example.org"},
    }


def test_get_storage_options_without_s3_config(monkeypatch):
    monkeypatch.setattr(config, "CONFIG", {})

    options = helpers.get_storage_options(source(None, "s3://bucket/file.nc"))

    assert options == {}


def test_get_storage_options_does_not_depend_on_format(monkeypatch):
    monkeypatch.setattr(
        config,
        "CONFIG",
        {"s3": {"anon": "true", "endpoint_url": "https://s3.example.org"}},
    )

    options = helpers.get_storage_options(source(None, "s3://bucket/ref.json"))

    assert options["anon"] is True


def test_open_dataset_passes_s3_options_to_kerchunk(monkeypatch):
    calls = {}

    def fake_open(path, **kwargs):
        calls["path"] = path
        calls["kwargs"] = kwargs
        return "DATASET"

    monkeypatch.setattr(helpers, "open_xr_dataset", fake_open)
    monkeypatch.setattr(config, "CONFIG", {"s3": {"anon": "true"}})

    result = helpers.open_dataset(
        source(None, "s3://bucket/reference.json"), apply_fixes=False
    )

    assert result == "DATASET"
    assert calls == {
        "path": "s3://bucket/reference.json",
        "kwargs": {"target_options": {"anon": True}},
    }


def test_get_storage_options_skips_local_files(monkeypatch):
    monkeypatch.setattr(config, "get_s3_storage_options", lambda: pytest.fail())

    assert helpers.get_storage_options(source(None, "/data/file.nc")) == {}


def test_open_dataset_passes_s3_backend_kwargs(monkeypatch):
    calls = {"open_kwargs": None}

    def fake_open(file_paths, **kwargs):
        calls["open_kwargs"] = kwargs
        return "DATASET"

    monkeypatch.setattr(helpers, "open_xr_dataset", fake_open)
    monkeypatch.setattr(helpers, "is_kerchunk_file", lambda _: False)
    monkeypatch.setattr(helpers, "apply_dataset_fixes", lambda _ds_id, ds: ds)
    monkeypatch.setattr(
        config,
        "CONFIG",
        {"s3": {"anon": "true", "endpoint_url": "https://s3.example.org"}},
    )

    _ = helpers.open_dataset(
        source(None, "s3://example-bucket/path/file.nc"),
        apply_fixes=False,
    )

    assert calls["open_kwargs"] == {
        "backend_kwargs": {
            "storage_options": {
                "anon": True,
                "client_kwargs": {"endpoint_url": "https://s3.example.org"},
            }
        }
    }
