import rook.utils.ops.consolidate as consolidate


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

    def fail_dset_to_filepaths(_dset, force=False):
        raise AssertionError("dset_to_filepaths should not be called for s3 input")

    monkeypatch.setattr(consolidate, "get_project_name", fail_get_project_name)
    monkeypatch.setattr(consolidate, "get_catalog", fail_get_catalog)
    monkeypatch.setattr(consolidate, "dset_to_filepaths", fail_dset_to_filepaths)

    collection = DummyCollection(["s3://example-bucket/path/file.nc"])
    result = consolidate.consolidate(collection)

    assert result == {
        "s3://example-bucket/path/file.nc": ["s3://example-bucket/path/file.nc"]
    }
