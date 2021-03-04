from tests.smoke.utils import open_dataset


import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.online]


CMIP6_COLLECTION = (
    "c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
)


def test_smoke_get_capabilities(wps):
    caps = wps.getcapabilities()
    assert caps.identification.type == "WPS"
    processes = [p.identifier for p in caps.processes]
    assert "subset" in processes
    assert "average" in processes
    assert "orchestrate" in processes


def test_smoke_describe_process_subset(wps):
    process = wps.describeprocess("subset")
    assert process.identifier == "subset"
    inputs = [inpt.identifier for inpt in process.dataInputs]
    assert "collection" in inputs
    assert "time" in inputs
    assert "area" in inputs


def test_smoke_execute_subset(wps, tmp_path):
    inputs = [("collection", CMIP6_COLLECTION), ("time", "2020-01-01/2020-12-30")]
    url = wps.execute("subset", inputs)
    assert "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_20200116-20201216.nc" in url
    ds = open_dataset(url, tmp_path)
    assert "rlds" in ds.variables


def test_smoke_execute_subset_original_files(wps):
    inputs = [("collection", CMIP6_COLLECTION)]
    url = wps.execute("subset", inputs)
    assert "data.mips.copernicus-climate.eu" in url


def test_smoke_execute_subset_time_and_area_cross_meridian(wps):
    inputs = [
        ("collection", CMIP6_COLLECTION),
        ("time", "2020-01-01/2020-12-30"),
        ("area", "-50,-50,50,50"),
    ]
    url = wps.execute("subset", inputs)
    assert "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_20200116-20201216.nc" in url
