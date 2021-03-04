from tests.smoke.utils import open_dataset

from owslib.wps import ComplexDataInput
import json


import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.online]


CMIP6_COLLECTION = (
    "c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
)

CMIP5_COLLECTION = (
    "c3s-cmip5.output1.ICHEC.EC-EARTH.historical.day.atmos.day.r1i1p1.tas.latest"
)

WF_SUBSET_AVERAGE = json.dumps(
    {
        "doc": "subset+average on cmip6 rlds",
        "inputs": {"ds": [CMIP6_COLLECTION]},
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


def test_smoke_execute_average_time(wps):
    inputs = [("collection", CMIP6_COLLECTION), ("dims", "time")]
    url = wps.execute("average", inputs)
    assert "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_avg-t.nc" in url


def test_smoke_execute_orchestrate(wps):
    inputs = [
        ("workflow", ComplexDataInput(WF_SUBSET_AVERAGE)),
    ]
    url = wps.execute("orchestrate", inputs)
    assert "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_avg-t.nc" in url
