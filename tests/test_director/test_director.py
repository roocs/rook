import pytest
from pywps.app.exceptions import ProcessError

from clisops.exceptions import InvalidCollection

import rook.director.director as director_mod
from rook.director import Director


class FakeSearchResult:
    def __init__(self, records, download_records=None):
        self._records = records
        self._download_records = download_records or records

    def __len__(self):
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
            director_mod.config,
            "get_project_config",
            lambda _project: {"use_catalog": True},
        )
        monkeypatch.setattr(director_mod, "get_catalog", lambda _project: catalog)
        return catalog

    return _catalog_director


class TestDirectorCMIP6:

    collection = [
        "c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    ]

    def test_project(self):
        inputs = {}
        d = Director(self.collection, inputs)
        assert d.project == "c3s-cmip6"

    def test_original_files(self):
        # original files
        inputs = {"original_files": True}
        d = Director(self.collection, inputs)
        assert d.use_original_files is True
        assert list(d.original_file_urls.items())[0][1] == [
            "https://data.mips.climate.copernicus.eu/thredds/fileServer"
            "/esg_c3s-cmip6"
            "/ScenarioMIP/INM/INM-CM5-0/ssp245/r1i1p1f1/Amon/rlds/gr1/v20190619"
            "/rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_201501-210012.nc"
        ]

    @pytest.mark.skip(reason="not relevant")
    def test_pre_checked_not_characterised(self):
        # raise exception
        inputs = {"pre_checked": True}
        with pytest.raises(ProcessError):
            Director(self.collection, inputs)

    def apply_fixes_not_required(self):
        # no subset so original files
        inputs = {"apply_fixes": True}
        d = Director(self.collection, inputs)
        assert d.use_original_files is True
        assert list(d.original_file_urls.items())[0][1] == [
            "https://data.mips.climate.copernicus.eu/thredds/fileServer"
            "/esg_c3s-cmip6/CMIP/IPSL/IPSL-CM6A-LR/historical"
            "/r1i1p1f1/Amon/rlds/gr/v20180803/rlds_Amon_"
            "IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc"
        ]

    def test_area_or_level(self):
        # WPS output
        inputs = {"area": "0.,49.,10.,65"}
        d = Director(self.collection, inputs)
        assert d.use_original_files is False

    @pytest.mark.xfail(reason="no CMIP6 test data in /pool/data")
    def test_time_subset_aligned(self):
        # original files
        inputs = {"time": "2015-01-01/2100-12-31"}
        d = Director(self.collection, inputs)
        assert d.use_original_files is True
        assert list(d.original_file_urls.items())[0][1] == [
            "https://data.mips.climate.copernicus.eu/thredds/fileServer"
            "/esg_c3s-cmip6"
            "/ScenarioMIP/INM/INM-CM5-0/ssp245/r1i1p1f1/Amon/rlds/gr1/v20190619"
            "/rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_201501-210012.nc"
        ]

    @pytest.mark.xfail(reason="no CMIP6 test data in /pool/data")
    def test_only_time_no_match(self):
        inputs = {"time": "2015-01-01/2100-11-30"}
        d = Director(self.collection, inputs)
        assert d.use_original_files is False

    def test_invalid_collection(self):
        inputs = {"time": "2015-01-01/2100-11-30"}
        with pytest.raises(InvalidCollection):
            Director(
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
        d = Director(self.collection, inputs)
        assert d.use_original_files is False
        assert d.original_file_urls is None
        assert d.output_uris is None


def test_catalog_collection_is_resolved_and_processed(tmp_path, catalog_director):
    collection = ["c3s-cmip6.example.dataset"]
    source = tmp_path / "input.nc"
    source.touch()
    result = FakeSearchResult({collection[0]: [source.as_posix()]})
    catalog = catalog_director(result)
    inputs = {"area": "0,0,10,10", "pre_checked": False, "original_files": False}
    captured = {}

    director = Director(collection, inputs)

    def runner(runner_inputs):
        captured["inputs"] = runner_inputs
        return ["processed.nc"]

    director.process(runner)

    assert catalog.search_kwargs == {
        "collection": collection,
        "time": None,
        "time_components": None,
    }
    assert director.use_original_files is False
    assert director.output_uris == ["processed.nc"]
    assert "pre_checked" not in captured["inputs"]
    assert "original_files" not in captured["inputs"]
    assert len(captured["inputs"]["collection"]) == 1


def test_catalog_original_files_are_returned_when_requested(catalog_director):
    collection = ["c3s-cmip6.example.dataset"]
    download_url = "https://example.test/data/input.nc"
    result = FakeSearchResult(
        {collection[0]: ["/data/input.nc"]},
        download_records={collection[0]: [download_url]},
    )
    catalog_director(result)

    director = Director(collection, {"original_files": True})
    director.process(lambda _inputs: pytest.fail("runner should not be called"))

    assert director.use_original_files is True
    assert director.output_uris == [download_url]


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

    monkeypatch.setattr(director_mod, "SubsetAlignmentChecker", AlignedFakeAlignment)

    director = Director(collection, {"time": "2001-01-01/2001-12-31"})
    director.process(lambda _inputs: pytest.fail("runner should not be called"))

    assert director.use_original_files is True
    assert director.output_uris == aligned_urls


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

    monkeypatch.setattr(director_mod, "SubsetAlignmentChecker", NotAlignedFakeAlignment)

    director = Director(collection, {"time": "2001-02-01/2001-02-28"})
    director.process(lambda _inputs: ["subset.nc"])

    assert director.use_original_files is False
    assert director.output_uris == ["subset.nc"]


@pytest.mark.parametrize(
    "operation_input", [{"dims": "time"}, {"freq": "year"}, {"grid": "1x1"}]
)
def test_catalog_operations_that_change_data_are_always_processed(
    catalog_director, monkeypatch, operation_input
):
    collection = ["c3s-cmip6.example.dataset"]
    result = FakeSearchResult(
        {collection[0]: ["/data/input.nc"]},
        download_records={collection[0]: ["https://example.test/data/input.nc"]},
    )
    catalog_director(result)
    monkeypatch.setattr(
        director_mod,
        "SubsetAlignmentChecker",
        lambda _urls, _inputs: pytest.fail("alignment should not be checked"),
    )

    director = Director(collection, operation_input)

    assert director.use_original_files is False
    assert director.original_file_urls is None


def test_catalog_unknown_collection_raises_invalid_collection(catalog_director):
    collection = ["c3s-cmip6.example.dataset"]
    catalog_director(FakeSearchResult({}))

    with pytest.raises(InvalidCollection):
        Director(collection, {})


def test_catalog_pre_checked_requires_characterised_data(catalog_director):
    collection = ["c3s-cmip6.example.dataset"]
    catalog_director(FakeSearchResult({collection[0]: ["/data/input.nc"]}))

    with pytest.raises(ProcessError, match="Data has not been pre-checked"):
        Director(collection, {"pre_checked": True})


# need to test a  different dataset that has been characterised:

# def test_apply_fixes_required(self):
#     # wps output - can't test this with this dataset
#     inputs = {"apply_fixes": True}
#     pass
#     d = Director(self.collection, inputs)
#     assert d.use_original_files is False
#
#
# def test_pre_checked_charactersied(self):
#     # fine - can't test this with this dataset
#     inputs = {"pre_checked": True}
#     pass
#     d = Director(self.collection, inputs)
