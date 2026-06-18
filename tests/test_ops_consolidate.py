import rook.utils.ops.consolidate as consolidate
from rook import config
from rook.catalog.base import Result
from rook.io.datasets import DatasetSource


class DummyCollection:
    def __init__(self, value):
        self.value = value


def test_consolidate_kerchunk_bypasses_catalog(monkeypatch):
    def fail_get_catalog(_project):
        raise AssertionError("Catalog lookup should not be called for kerchunk input")

    monkeypatch.setattr(consolidate, "get_catalog", fail_get_catalog)

    collection = DummyCollection(["https://example.org/refs/mydataset.json"])
    result = consolidate.consolidate(collection)

    assert result == (
        DatasetSource(
            dataset_id=None,
            paths=("https://example.org/refs/mydataset.json",),
        ),
    )


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

    assert result == (
        DatasetSource(
            dataset_id=None,
            paths=("s3://example-bucket/path/file.nc",),
        ),
    )


def test_consolidate_zarr_bypasses_catalog_and_mapper(monkeypatch):
    def fail_lookup(*_args, **_kwargs):
        raise AssertionError("Catalog and file lookup should not run for Zarr input")

    monkeypatch.setattr(consolidate, "get_project_name", fail_lookup)
    monkeypatch.setattr(consolidate, "get_catalog", fail_lookup)
    monkeypatch.setattr(consolidate, "dset_to_filepaths", fail_lookup)

    store = "s3://example-bucket/path/example.zarr"
    collection = DummyCollection([store])
    result = consolidate.consolidate(collection)

    assert result == (DatasetSource(dataset_id=None, paths=(store,)),)


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
        config,
        "_CONFIG",
        {
            "project:c3s-cmip6": {"base_dir": "/data/CMIP6"},
            "s3": {"base_dir": "s3://example-bucket/data/CMIP6"},
        },
    )

    collection = DummyCollection(["c3s-cmip6.dataset"])
    result = consolidate.consolidate(collection)

    assert result == (
        DatasetSource(
            dataset_id="c3s-cmip6.dataset",
            paths=(
                "s3://example-bucket/data/CMIP6/ScenarioMIP/Model/file_201501-210012.nc",
            ),
        ),
    )


def test_consolidate_resolves_mixed_sources_independently(monkeypatch):
    catalog_calls = []

    class DummyResult:
        def __init__(self, dataset_id):
            self.dataset_id = dataset_id

        def __len__(self):
            return 1

        def files(self):
            return {self.dataset_id: [f"/data/{self.dataset_id}.nc"]}

    class DummyCatalog:
        def search(self, collection, time):
            assert time is None
            return DummyResult(collection)

    def fake_get_catalog(project):
        catalog_calls.append(project)
        return DummyCatalog()

    monkeypatch.setattr(consolidate, "get_project_name", lambda _dset: "project")
    monkeypatch.setattr(consolidate, "derive_ds_id", lambda dset: dset)
    monkeypatch.setattr(consolidate, "get_catalog", fake_get_catalog)

    collection = DummyCollection(
        ["s3://bucket/direct.nc", "project.one", "project.two"]
    )

    assert consolidate.consolidate(collection) == (
        DatasetSource(dataset_id=None, paths="s3://bucket/direct.nc"),
        DatasetSource(dataset_id="project.one", paths="/data/project.one.nc"),
        DatasetSource(dataset_id="project.two", paths="/data/project.two.nc"),
    )
    assert catalog_calls == ["project"]
