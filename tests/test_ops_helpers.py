import xarray as xr

import rook.utils.ops.helpers as helpers


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

    result = helpers.open_dataset("project.dataset", ["a.nc"], apply_fixes=True)

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

    result = helpers.open_dataset("project.dataset", ["a.nc"], apply_fixes=False)

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

    result = helpers.open_dataset("kerchunk.json", ["a.nc"], apply_fixes=True)

    assert result == "DATASET"
    assert calls == {"open": 1, "fix": 0}


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


def test_is_s3_uri_true():
    assert helpers.is_s3_uri("s3://my-bucket/path/file.nc") is True


def test_is_s3_uri_false_for_https():
    assert helpers.is_s3_uri("https://example.org/file.nc") is False


def test_is_zarr_store_local_path():
    assert helpers.is_zarr_store("/data/example.zarr") is True


def test_is_zarr_store_url_with_query_and_trailing_slash():
    assert helpers.is_zarr_store("s3://bucket/example.zarr/?token=abc") is True


def test_is_zarr_store_netcdf_path():
    assert helpers.is_zarr_store("s3://bucket/example.nc") is False


def test_get_zarr_store_from_catalog_file_paths():
    assert helpers.get_zarr_store(
        "project.dataset", ["s3://bucket/example.zarr"]
    ) == "s3://bucket/example.zarr"


def test_open_dataset_opens_local_zarr_store(tmp_path):
    store = tmp_path / "example.zarr"
    expected = xr.Dataset({"tas": ("time", [280.0, 281.0])})
    expected.to_zarr(store, mode="w")

    result = helpers.open_dataset(str(store), str(store), apply_fixes=False)

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
        "project.dataset", [str(path)], apply_fixes=False
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
        helpers,
        "CONFIG",
        {"s3": {"anon": "true", "endpoint_url": "https://s3.example.org"}},
    )

    result = helpers.open_dataset(
        "s3://example-bucket/path/example.zarr",
        "s3://example-bucket/path/example.zarr",
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
        "/data/example.zarr", "/data/example.zarr", apply_fixes=True
    )

    assert result == "DATASET"


def test_get_s3_open_kwargs_for_s3_netcdf(monkeypatch):
    monkeypatch.setattr(
        helpers,
        "CONFIG",
        {"s3": {"anon": "true", "endpoint_url": "https://s3.example.org"}},
    )

    kwargs = helpers.get_s3_open_kwargs(
        "s3://example-bucket/path/file.nc", ["s3://example-bucket/path/file.nc"]
    )

    assert kwargs == {
        "backend_kwargs": {
            "storage_options": {
                "anon": True,
                "client_kwargs": {"endpoint_url": "https://s3.example.org"},
            }
        }
    }


def test_get_s3_open_kwargs_without_s3_config(monkeypatch):
    monkeypatch.setattr(helpers, "CONFIG", {})

    kwargs = helpers.get_s3_open_kwargs(
        "s3://example-bucket/path/file.nc", ["s3://example-bucket/path/file.nc"]
    )

    assert kwargs == {}


def test_get_s3_open_kwargs_skips_kerchunk(monkeypatch):
    monkeypatch.setattr(
        helpers,
        "CONFIG",
        {"s3": {"anon": "true", "endpoint_url": "https://s3.example.org"}},
    )

    kwargs = helpers.get_s3_open_kwargs(
        "s3://example-bucket/path/ref.json", ["s3://example-bucket/path/ref.json"]
    )

    assert kwargs == {}


def test_get_s3_storage_options_merges_client_kwargs(monkeypatch):
    monkeypatch.setattr(
        helpers,
        "CONFIG",
        {
            "s3": {
                "storage_options_json": '{"anon": true, "client_kwargs": {"region_name": "eu-west-1"}}',
                "client_kwargs_json": '{"use_ssl": false}',
                "endpoint_url": "https://s3.example.org",
            }
        },
    )

    assert helpers.get_s3_storage_options() == {
        "anon": True,
        "client_kwargs": {
            "region_name": "eu-west-1",
            "use_ssl": False,
            "endpoint_url": "https://s3.example.org",
        },
    }


def test_open_dataset_passes_s3_backend_kwargs(monkeypatch):
    calls = {"open_kwargs": None}

    def fake_open(file_paths, **kwargs):
        calls["open_kwargs"] = kwargs
        return "DATASET"

    monkeypatch.setattr(helpers, "open_xr_dataset", fake_open)
    monkeypatch.setattr(helpers, "is_kerchunk_file", lambda _: False)
    monkeypatch.setattr(helpers, "apply_dataset_fixes", lambda _ds_id, ds: ds)
    monkeypatch.setattr(
        helpers,
        "CONFIG",
        {"s3": {"anon": "true", "endpoint_url": "https://s3.example.org"}},
    )

    _ = helpers.open_dataset(
        "s3://example-bucket/path/file.nc",
        ["s3://example-bucket/path/file.nc"],
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
