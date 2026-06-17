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
