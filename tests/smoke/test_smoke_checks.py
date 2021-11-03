from tests.smoke.utils import open_dataset

from owslib.wps import ComplexDataInput
import json


import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.online]


C3S_CMIP6_MON_COLLECTION = (
    "c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
)

C3S_CMIP6_DAY_COLLECTION = (
    "c3s-cmip6.ScenarioMIP.MOHC.HadGEM3-GC31-LL.ssp245.r1i1p1f3.day.tas.gn.v20190908"
)

CMIP5_COLLECTION = (
    "c3s-cmip5.output1.ICHEC.EC-EARTH.historical.day.atmos.day.r1i1p1.tas.latest"
)

WF_SUBSET_AVERAGE = json.dumps(
    {
        "doc": "subset+average on cmip6 rlds",
        "inputs": {"ds": [C3S_CMIP6_MON_COLLECTION]},
        "outputs": {"output": "average_ds/output"},
        "steps": {
            "subset_ds": {
                "run": "subset",
                "in": {"collection": "inputs/ds", "time": "2020-01-01/2020-12-31"},
            },
            "average_ds": {
                "run": "average",
                "in": {"collection": "subset_ds/output", "dims": "time"},
            },
        },
    }
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


def test_smoke_describe_process_average(wps):
    process = wps.describeprocess("average")
    assert process.identifier == "average"
    inputs = [inpt.identifier for inpt in process.dataInputs]
    assert "collection" in inputs
    assert "dims" in inputs


def test_smoke_describe_process_orchestrate(wps):
    process = wps.describeprocess("orchestrate")
    assert process.identifier == "orchestrate"
    inputs = [inpt.identifier for inpt in process.dataInputs]
    assert "workflow" in inputs


def test_smoke_execute_subset(wps, tmp_path):
    inputs = [
        ("collection", C3S_CMIP6_MON_COLLECTION),
        ("time", "2020-01-01/2020-12-30"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_20200116-20201216.nc" in urls[0]
    ds = open_dataset(urls[0], tmp_path)
    assert "rlds" in ds.variables


def test_smoke_execute_subset_by_point(wps, tmp_path):
    inputs = [
        ("collection", C3S_CMIP6_MON_COLLECTION),
        ("time", "2020-01-01/2020-12-30"),
        ("time_components", "month:jan,feb,mar"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_20200116-20200316.nc" in urls[0]
    ds = open_dataset(urls[0], tmp_path)
    assert "rlds" in ds.variables


def test_smoke_execute_subset_original_files(wps):
    inputs = [
        ("collection", C3S_CMIP6_DAY_COLLECTION),
        ("time", "2020-01-01/2020-12-30"),
        ("original_files", "1"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "data.mips.copernicus-climate.eu" in urls[0]


def test_smoke_execute_subset_collection_only(wps):
    inputs = [("collection", C3S_CMIP6_DAY_COLLECTION)]
    urls = wps.execute("subset", inputs)
    print(urls)
    assert len(urls) == 2
    assert "data.mips.copernicus-climate.eu" in urls[0]


def test_smoke_execute_subset_time_and_area_cross_meridian(wps):
    inputs = [
        ("collection", C3S_CMIP6_MON_COLLECTION),
        ("time", "2020-01-01/2020-12-30"),
        ("area", "-50,-50,50,50"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_20200116-20201216.nc" in urls[0]


def test_smoke_execute_c3s_cmip6_mon_average_time(wps):
    inputs = [("collection", C3S_CMIP6_MON_COLLECTION), ("dims", "time")]
    urls = wps.execute("average", inputs)
    assert len(urls) == 1
    assert "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_avg-t.nc" in urls[0]


def test_smoke_execute_c3s_cmip6_day_average_time(wps):
    inputs = [("collection", C3S_CMIP6_DAY_COLLECTION), ("dims", "time")]
    urls = wps.execute("average", inputs)
    print(urls)
    assert len(urls) == 1
    assert "tas_day_HadGEM3-GC31-LL_ssp245_r1i1p1f3_gn_avg-t.nc" in urls[0]


def test_smoke_execute_orchestrate(wps):
    inputs = [
        ("workflow", ComplexDataInput(WF_SUBSET_AVERAGE)),
    ]
    urls = wps.execute("orchestrate", inputs)
    assert len(urls) == 1
    assert "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_avg-t.nc" in urls[0]
