import rook.utils.ops.consolidate as consolidate
from rook.catalog import base
from rook.catalog.base import Result


class DummyCollection:
    def __init__(self, value):
        self.value = value


def test_consolidate_kerchunk_bypasses_catalog(monkeypatch):
    def fail_get_catalog(_project):
        raise AssertionError("Catalog lookup should not be called for kerchunk input")

    monkeypatch.setattr(consolidate, "get_catalog", fail_get_catalog)

    collection = DummyCollection(["https://example.org/refs/mydataset.json"])
    result = consolidate.consolidate(collection)

    assert result == {
        "https://example.org/refs/mydataset.json": "https://example.org/refs/mydataset.json"
    }


def test_consolidate_s3_bypasses_catalog_and_mapper(monkeypatch):
    def fail_get_project_name(_dset):
        raise AssertionError("Project lookup should not be called for s3 input")

    def fail_get_catalog(_project):
        raise AssertionError("Catalog lookup should not be called for s3 input")

    def fail_dset_to_filepaths(_dset, **_kwargs):
        raise AssertionError("dset_to_filepaths should not be called for s3 input")

    monkeypatch.setattr(consolidate, "get_project_name", fail_get_project_name)
    monkeypatch.setattr(consolidate, "get_catalog", fail_get_catalog)
    monkeypatch.setattr(consolidate, "dset_to_filepaths", fail_dset_to_filepaths)

    collection = DummyCollection(["s3://example-bucket/path/file.nc"])
    result = consolidate.consolidate(collection)

    assert result == {
        "s3://example-bucket/path/file.nc": ["s3://example-bucket/path/file.nc"]
    }


def test_consolidate_catalog_files_can_use_s3_base_dir(monkeypatch):
    class DummyCatalog:
        def search(self, collection, time):
            assert collection == "dataset"
            assert time is None
            return Result(
                "c3s-cmip6",
                {"c3s-cmip6.dataset": ["ScenarioMIP/Model/file_201501-210012.nc"]},
            )

    monkeypatch.setattr(consolidate, "get_project_name", lambda _dset: "c3s-cmip6")
    monkeypatch.setattr(consolidate, "derive_ds_id", lambda _dset: "dataset")
    monkeypatch.setattr(consolidate, "get_catalog", lambda _project: DummyCatalog())
    monkeypatch.setattr(
        base,
        "CONFIG",
        {
            "project:c3s-cmip6": {"base_dir": "/data/CMIP6"},
            "s3": {"base_dir": "s3://example-bucket/data/CMIP6"},
        },
    )

    collection = DummyCollection(["c3s-cmip6.dataset"])
    result = consolidate.consolidate(collection)

    assert result == {
        "c3s-cmip6.dataset": [
            "s3://example-bucket/data/CMIP6/ScenarioMIP/Model/file_201501-210012.nc"
        ]
    }
