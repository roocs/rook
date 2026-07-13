import pytest
import types

from rook.catalog.intake import IntakeCatalog

C3S_CMIP6_DAY_COLLECTION = (
    "c3s-cmip6.CMIP.SNU.SAM0-UNICON.historical.r1i1p1f1.day.pr.gn.v20190323"
)
C3S_CMIP6_MON_COLLECTION = (
    "c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
)
C3S_CMIP6_FX_COLLECTION = (
    "c3s-cmip6.ScenarioMIP.MRI.MRI-ESM2-0.ssp370.r1i1p1f1.fx.orog.gn.v20190603"
)


@pytest.mark.mini_esgf_data
@pytest.mark.usefixtures("load_test_data")
def test_intake_catalog_c3s_cmip6_mon(stratus):
    cat = IntakeCatalog(project="c3s-cmip6")
    result = cat.search(collection=C3S_CMIP6_MON_COLLECTION)
    assert result.matches == 1
    files = result.files()[C3S_CMIP6_MON_COLLECTION]
    assert len(files) == 1
    expected_suffix = (
        "ScenarioMIP/INM/INM-CM5-0/ssp245/r1i1p1f1/Amon/rlds/gr1/v20190619/"
        "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_201501-210012.nc"
    )
    assert files[0].endswith(expected_suffix)
    # check download url
    urls = result.download_urls()[C3S_CMIP6_MON_COLLECTION]
    expected_url = (
        "https://data.mips.climate.copernicus.eu/thredds/fileServer/esg_c3s-cmip6/"
        "ScenarioMIP/INM/INM-CM5-0/ssp245/r1i1p1f1/Amon/rlds/gr1/v20190619/"
        "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_201501-210012.nc"
    )
    assert expected_url == urls[0]


@pytest.mark.mini_esgf_data
@pytest.mark.usefixtures("load_test_data")
def test_intake_catalog_c3s_cmip6_day():
    cat = IntakeCatalog(project="c3s-cmip6")
    # all files
    result = cat.search(collection=C3S_CMIP6_DAY_COLLECTION)
    assert result.matches == 1
    files = result.files()[C3S_CMIP6_DAY_COLLECTION]
    assert len(files) == 165
    # one year only
    result = cat.search(
        collection=C3S_CMIP6_DAY_COLLECTION,
        time="1900-01-01/1900-12-31",
    )
    assert result.matches == 1
    files = result.files()[C3S_CMIP6_DAY_COLLECTION]
    assert len(files) == 1
    assert "CMIP/SNU/SAM0-UNICON/historical/r1i1p1f1/day/pr/gn/v20190323" in files[0]
    assert "pr_day_SAM0-UNICON_historical_r1i1p1f1_gn_19000101-19001231.nc" in files[0]


@pytest.mark.mini_esgf_data
@pytest.mark.usefixtures("load_test_data")
def test_intake_catalog_c3s_cmip6_fx():
    cat = IntakeCatalog(project="c3s-cmip6")
    result = cat.search(collection=C3S_CMIP6_FX_COLLECTION)
    # all files
    assert result.matches == 1
    files = result.files()[C3S_CMIP6_FX_COLLECTION]
    assert len(files) == 1
    assert "ScenarioMIP/MRI/MRI-ESM2-0/ssp370/r1i1p1f1/fx/orog/gn/v20190603" in files[0]
    assert "orog_fx_MRI-ESM2-0_ssp370_r1i1p1f1_gn.nc" in files[0]
    # filter by time should have no effect ... to time axis
    result = cat.search(
        collection=C3S_CMIP6_FX_COLLECTION,
        time="2000-01-01/2010-12-31",
    )
    assert result.matches == 1
    files = result.files()[C3S_CMIP6_FX_COLLECTION]
    assert len(files) == 1


@pytest.mark.mini_esgf_data
@pytest.mark.usefixtures("load_test_data")
def test_intake_catalog_c3s_cmip6_multiple():
    cat = IntakeCatalog(project="c3s-cmip6")
    result = cat.search(collection=[C3S_CMIP6_MON_COLLECTION, C3S_CMIP6_FX_COLLECTION])
    assert result.matches == 2
    files = result.files()[C3S_CMIP6_MON_COLLECTION]
    assert len(files) == 1
    files = result.files()[C3S_CMIP6_FX_COLLECTION]
    assert len(files) == 1


def test_intake_catalog_uses_proxy_aware_http_fs(monkeypatch):
    calls = {}

    class DummyProjectCatalog:
        def read(self):
            return "ok"

    def fake_open_catalog(url, **kwargs):
        calls["url"] = url
        calls["kwargs"] = kwargs
        return {"c3s-cmip6": DummyProjectCatalog()}

    def fake_filesystem(protocol, client_kwargs):
        calls["protocol"] = protocol
        calls["client_kwargs"] = client_kwargs
        return "dummy-fs"

    monkeypatch.setattr("rook.catalog.intake.intake.open_catalog", fake_open_catalog)
    monkeypatch.setattr(
        "rook.catalog.intake.fsspec",
        types.SimpleNamespace(filesystem=fake_filesystem),
    )

    cat = IntakeCatalog(project="c3s-cmip6", url="https://example.com/catalog.yml")
    _ = cat.catalog

    assert calls["url"] == "https://example.com/catalog.yml"
    assert calls["protocol"] == "http"
    assert calls["client_kwargs"] == {"trust_env": True}
    assert calls["kwargs"]["fs"] == "dummy-fs"
    assert calls["kwargs"]["getshell"] is False


def test_intake_catalog_resets_project_storage_options(monkeypatch):
    class DummyProjectCatalog:
        _storage_options = {"foo": "bar"}

        def read(self):
            assert self._storage_options is None
            return "ok"

    def fake_open_catalog(_url, **_kwargs):
        return {"c3s-cmip6": DummyProjectCatalog()}

    monkeypatch.setattr("rook.catalog.intake.intake.open_catalog", fake_open_catalog)

    cat = IntakeCatalog(project="c3s-cmip6", url="https://example.com/catalog.yml")
    assert cat.load() == "ok"


def test_intake_catalog_disables_shell_expansion_for_local_catalog(monkeypatch):
    calls = {}

    def fake_open_catalog(url, **kwargs):
        calls["url"] = url
        calls["kwargs"] = kwargs
        return {}

    monkeypatch.setattr("rook.catalog.intake.intake.open_catalog", fake_open_catalog)

    cat = IntakeCatalog(project="c3s-cmip6", url="catalog.yml")
    _ = cat.catalog

    assert calls["url"] == "catalog.yml"
    assert calls["kwargs"]["getshell"] is False
