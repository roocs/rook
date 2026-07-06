import pytest
from clisops.exceptions import InvalidCollection

import rook.director.planning as planning_mod
from rook.director import execute_planned_request, wrap_director


class FakeSearchResult:
    def __init__(self, records, download_records=None):
        self._records = records
        self._download_records = download_records or records

    def __len__(self):
        """Return the number of matched catalog records."""
        return len(self._records)

    def files(self):
        return self._records

    def download_urls(self):
        return self._download_records


class FakeCatalog:
    def __init__(self, search_result):
        self.search_result = search_result
        self.search_kwargs = None

    def search(self, **kwargs):
        self.search_kwargs = kwargs
        return self.search_result


class FakeAlignment:
    is_aligned = True
    aligned_files = []

    def __init__(self, input_files, inputs):
        self.input_files = input_files
        self.inputs = inputs


@pytest.fixture
def catalog_director(monkeypatch):
    def _catalog_director(search_result):
        catalog = FakeCatalog(search_result)
        monkeypatch.setattr(
            planning_mod.config,
            "get_project_config",
            lambda _project: {"use_catalog": True},
        )
        monkeypatch.setattr(planning_mod, "get_catalog", lambda _project: catalog)
        return catalog

    return _catalog_director


class TestDirectorCMIP6:

    collection = [
        "c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    ]

    def test_project(self, monkeypatch):
        inputs = {}
        monkeypatch.setattr(
            planning_mod.config,
            "get_project_config",
            lambda _project: {"use_catalog": False},
        )
        plan = planning_mod.plan_request(self.collection, inputs)
        assert plan.project == "c3s-cmip6"
        assert isinstance(plan, planning_mod.RunOperation)

    def test_original_files(self, catalog_director):
        # original files
        inputs = {"original_files": True}
        url = (
            "https://data.mips.climate.copernicus.eu/thredds/fileServer"
            "/esg_c3s-cmip6"
            "/ScenarioMIP/INM/INM-CM5-0/ssp245/r1i1p1f1/Amon/rlds/gr1/v20190619"
            "/rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_201501-210012.nc"
        )
        catalog_director(
            FakeSearchResult(
                {self.collection[0]: ["/data/input.nc"]},
                download_records={self.collection[0]: [url]},
            )
        )
        plan = planning_mod.plan_request(self.collection, inputs)
        assert plan.returns_original_files is True
        assert isinstance(plan, planning_mod.ReturnOriginalFiles)
        assert list(plan.original_file_urls.items())[0][1] == [url]

    def test_area_or_level(self, tmp_path, catalog_director):
        # WPS output
        inputs = {"area": "0.,49.,10.,65"}
        source = tmp_path / "input.nc"
        source.touch()
        catalog_director(FakeSearchResult({self.collection[0]: [source.as_posix()]}))
        plan = planning_mod.plan_request(self.collection, inputs)
        assert plan.returns_original_files is False

    @pytest.mark.xfail(reason="no CMIP6 test data in /pool/data")
    def test_time_subset_aligned(self):
        # original files
        inputs = {"time": "2015-01-01/2100-12-31"}
        plan = planning_mod.plan_request(self.collection, inputs)
        assert plan.returns_original_files is True
        assert list(plan.original_file_urls.items())[0][1] == [
            "https://data.mips.climate.copernicus.eu/thredds/fileServer"
            "/esg_c3s-cmip6"
            "/ScenarioMIP/INM/INM-CM5-0/ssp245/r1i1p1f1/Amon/rlds/gr1/v20190619"
            "/rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_201501-210012.nc"
        ]

    @pytest.mark.xfail(reason="no CMIP6 test data in /pool/data")
    def test_only_time_no_match(self):
        inputs = {"time": "2015-01-01/2100-11-30"}
        plan = planning_mod.plan_request(self.collection, inputs)
        assert plan.returns_original_files is False

    def test_invalid_collection(self, catalog_director):
        inputs = {"time": "2015-01-01/2100-11-30"}
        catalog_director(FakeSearchResult({}))
        with pytest.raises(InvalidCollection):
            planning_mod.plan_request(
                [
                    "c3s-cmip6.ScenarioMIP.INM.INVALID.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
                ],
                inputs,
            )


# Any combinations ?


class TestDirector:

    collection = ["CMIP6.CMIP.NCAR.CESM2.amip.r3i1p1f1.Amon.cl.gn.v20190319"]

    def test_no_inventory(self):
        # use_inventory for CMIP6 is set to False
        inputs = {"time": "1850-01-01/2014-12-01"}
        plan = planning_mod.plan_request(self.collection, inputs)
        assert plan.returns_original_files is False
        assert plan.original_file_urls is None


def test_catalog_collection_is_resolved_and_processed(tmp_path, catalog_director):
    collection = ["c3s-cmip6.example.dataset"]
    source = tmp_path / "input.nc"
    source.touch()
    result = FakeSearchResult({collection[0]: [source.as_posix()]})
    catalog = catalog_director(result)
    inputs = {"area": "0,0,10,10", "pre_checked": False, "original_files": False}
    captured = {}

    def runner(runner_inputs):
        captured["inputs"] = runner_inputs
        return ["processed.nc"]

    result = execute_planned_request(collection, inputs, runner)

    assert catalog.search_kwargs == {
        "collection": collection,
        "time": None,
        "time_components": None,
    }
    assert result.use_original_files is False
    assert len(result.plan.dataset_sources) == 1
    assert result.plan.dataset_sources[0].dataset_id == collection[0]
    assert result.output_uris == ["processed.nc"]
    assert inputs == {
        "area": "0,0,10,10",
        "pre_checked": False,
        "original_files": False,
    }
    assert "pre_checked" not in captured["inputs"]
    assert "original_files" not in captured["inputs"]
    assert len(captured["inputs"]["collection"]) == 1
    assert captured["inputs"]["collection"][0].dataset_id == collection[0]


def test_catalog_collection_source_is_named(catalog_director):
    collection = ["c3s-cmip6.example.dataset"]
    catalog_director(FakeSearchResult({collection[0]: ["/data/input.nc"]}))

    source = planning_mod.classify_request_source(collection)

    assert isinstance(source, planning_mod.CatalogCollection)
    assert source.collection == collection
    assert source.project == "c3s-cmip6"


def test_non_catalog_collection_source_is_direct(monkeypatch):
    collection = ["CMIP6.CMIP.NCAR.CESM2.amip.r3i1p1f1.Amon.cl.gn.v20190319"]
    monkeypatch.setattr(
        planning_mod.config,
        "get_project_config",
        lambda _project: {"use_catalog": False},
    )

    source = planning_mod.classify_request_source(collection)
    plan = planning_mod.plan_request(collection, {})

    assert isinstance(source, planning_mod.DirectDataset)
    assert source.collection == collection
    assert source.project == "cmip6"
    assert isinstance(plan, planning_mod.RunOperation)
    assert plan.search_result is None
    assert plan.dataset_sources == ()


def test_execute_planned_request_returns_request_result(tmp_path, catalog_director):
    collection = ["c3s-cmip6.example.dataset"]
    source = tmp_path / "input.nc"
    source.touch()
    catalog_director(FakeSearchResult({collection[0]: [source.as_posix()]}))

    result = execute_planned_request(
        collection, {"area": "0,0,10,10"}, lambda _inputs: ["out.nc"]
    )

    assert result.output_uris == ["out.nc"]
    assert result.use_original_files is False
    assert result.dataset_sources[0].dataset_id == collection[0]


def test_wrap_director_alias_returns_request_result(tmp_path, catalog_director):
    collection = ["c3s-cmip6.example.dataset"]
    source = tmp_path / "input.nc"
    source.touch()
    catalog_director(FakeSearchResult({collection[0]: [source.as_posix()]}))

    result = wrap_director(collection, {"area": "0,0,10,10"}, lambda _inputs: ["out.nc"])

    assert result.output_uris == ["out.nc"]


def test_catalog_original_files_are_returned_when_requested(catalog_director):
    collection = ["c3s-cmip6.example.dataset"]
    download_url = "https://example.test/data/input.nc"
    result = FakeSearchResult(
        {collection[0]: ["/data/input.nc"]},
        download_records={collection[0]: [download_url]},
    )
    catalog_director(result)

    result = execute_planned_request(
        collection,
        {"original_files": True},
        lambda _inputs: pytest.fail("runner should not be called"),
    )

    assert result.use_original_files is True
    assert result.output_uris == [download_url]


def test_catalog_aligned_subset_returns_matching_original_files(
    catalog_director, monkeypatch
):
    collection = ["c3s-cmip6.example.dataset"]
    all_urls = [
        "https://example.test/data/input-2000.nc",
        "https://example.test/data/input-2001.nc",
    ]
    aligned_urls = [all_urls[1]]
    result = FakeSearchResult(
        {collection[0]: ["/data/input-2000.nc", "/data/input-2001.nc"]},
        download_records={collection[0]: all_urls},
    )
    catalog_director(result)

    class AlignedFakeAlignment(FakeAlignment):
        is_aligned = True
        aligned_files = aligned_urls

    monkeypatch.setattr(planning_mod, "SubsetAlignmentChecker", AlignedFakeAlignment)

    result = execute_planned_request(
        collection,
        {"time": "2001-01-01/2001-12-31"},
        lambda _inputs: pytest.fail("runner should not be called"),
    )

    assert result.use_original_files is True
    assert result.output_uris == aligned_urls


def test_catalog_non_aligned_subset_is_processed(
    tmp_path, catalog_director, monkeypatch
):
    collection = ["c3s-cmip6.example.dataset"]
    source = tmp_path / "input.nc"
    source.touch()
    result = FakeSearchResult(
        {collection[0]: [source.as_posix()]},
        download_records={collection[0]: ["https://example.test/data/input.nc"]},
    )
    catalog_director(result)

    class NotAlignedFakeAlignment(FakeAlignment):
        is_aligned = False
        aligned_files = []

    monkeypatch.setattr(planning_mod, "SubsetAlignmentChecker", NotAlignedFakeAlignment)

    result = execute_planned_request(
        collection, {"time": "2001-02-01/2001-02-28"}, lambda _inputs: ["subset.nc"]
    )

    assert result.use_original_files is False
    assert result.output_uris == ["subset.nc"]


@pytest.mark.parametrize(
    "operation_input", [{"dims": "time"}, {"freq": "year"}, {"grid": "1x1"}]
)
def test_catalog_operations_that_change_data_are_always_processed(
    tmp_path, catalog_director, monkeypatch, operation_input
):
    collection = ["c3s-cmip6.example.dataset"]
    source = tmp_path / "input.nc"
    source.touch()
    result = FakeSearchResult(
        {collection[0]: [source.as_posix()]},
        download_records={collection[0]: ["https://example.test/data/input.nc"]},
    )
    catalog_director(result)
    monkeypatch.setattr(
        planning_mod,
        "SubsetAlignmentChecker",
        lambda _urls, _inputs: pytest.fail("alignment should not be checked"),
    )

    plan = planning_mod.plan_request(collection, operation_input)

    assert plan.returns_original_files is False
    assert plan.original_file_urls is None


def test_catalog_unknown_collection_raises_invalid_collection(catalog_director):
    collection = ["c3s-cmip6.example.dataset"]
    catalog_director(FakeSearchResult({}))

    with pytest.raises(InvalidCollection):
        planning_mod.plan_request(collection, {})
