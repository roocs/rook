import json
from urllib.parse import urljoin

import pytest
import requests
from owslib.wps import ComplexDataInput, WebProcessingService

from rook.processes.wps_health import HEALTHY_RESPONSE

pytestmark = [pytest.mark.smoke, pytest.mark.online]


C3S_CMIP6_MON_COLLECTION = (
    "c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
)

C3S_CMIP6_DAY_COLLECTION = (
    "c3s-cmip6.ScenarioMIP.MOHC.HadGEM3-GC31-LL.ssp245.r1i1p1f3.day.tas.gn.v20190908"
)

C3S_CMIP6_DAY_HUSS_COLLECTION = (
    "c3s-cmip6.ScenarioMIP.EC-Earth-Consortium.EC-Earth3-CC.ssp245."
    "r1i1p1f1.day.huss.gr.v20210113"
)

C3S_CMIP6_MON_TASMIN_COLLECTION = (
    "c3s-cmip6.CMIP.MPI-M.MPI-ESM1-2-HR.historical.r1i1p1f1.Amon.tasmin.gn.v20190710"
)

C3S_CMIP6_MON_LEVEL_COLLECTION = (
    "c3s-cmip6.CMIP.CSIRO-ARCCSS.ACCESS-CM2.historical.r1i1p1f1.Amon.ta.gn.v20191108"
)

C3S_CMIP6_360DAY_CALENDAR_COLLECTION = (
    "c3s-cmip6.ScenarioMIP.MOHC.HadGEM3-GC31-LL.ssp245.r1i1p1f3.day.pr.gn.v20190908"
)

C3S_CMIP5_DAY_COLLECTION = (
    "c3s-cmip5.output1.IPSL.IPSL-CM5B-LR.historical.day.atmos.day.r1i1p1.tas.v20120718"
)

C3S_CMIP5_MON_COLLECTION = (
    "c3s-cmip5.output1.MPI-M.MPI-ESM-LR.historical.mon.atmos.Amon.r1i1p1.tas.v20120315"
)

C3S_CORDEX_DAY_COLLECTION = "c3s-cordex.output.EUR-11.IPSL.IPSL-IPSL-CM5A-MR.rcp85.r1i1p1.IPSL-WRF381P.v1.day.tas.v20190919"  # noqa

C3S_CORDEX_MON_COLLECTION = "c3s-cordex.output.EUR-11.CLMcom.MOHC-HadGEM2-ES.rcp85.r1i1p1.CLMcom-CCLM4-8-17.v1.mon.tas.v20150320"  # noqa

C3S_IPCC_ATLAS_CMIP5_COLLECTION = "c3s-ipcc-atlas.tnn.CMIP5.rcp45.mon"

C3S_IPCC_ATLAS_CMIP6_COLLECTION = "c3s-ipcc-atlas.tnn.CMIP6.historical.mon"

C3S_IPCC_ATLAS_CORDEX_COLLECTION = "c3s-ipcc-atlas.tnn.CORDEX-AFR.historical.mon"

C3S_CICA_ATLAS_ERA5_COLLECTION = "c3s-cica-atlas.cd.ERA5-Land.yr.v25"

C3S_CICA_ATLAS_CORDEX_COLLECTION = "c3s-cica-atlas.cdd.CORDEX-CORE.historical.yr.v25"

C3S_CICA_ATLAS_CMIP6_COLLECTION = "c3s-cica-atlas.cd.CMIP6.historical.yr.v25"

C3S_CMIP6_DECADAL_COLLECTIONS = (
    "c3s-cmip6-decadal.DCPP.MOHC.HadGEM3-GC31-MM.dcppA-hindcast.s1995-r1i1p1f2.Amon.tas.gn.v20200417",
    "c3s-cmip6-decadal.DCPP.MOHC.HadGEM3-GC31-MM.dcppA-hindcast.s1995-r2i1p1f2.Amon.tas.gn.v20200417",
    "c3s-cmip6-decadal.DCPP.MOHC.HadGEM3-GC31-MM.dcppA-hindcast.s1995-r3i1p1f2.Amon.tas.gn.v20200417",
    "c3s-cmip6-decadal.DCPP.MOHC.HadGEM3-GC31-MM.dcppA-hindcast.s1995-r4i1p1f2.Amon.tas.gn.v20200417",
    "c3s-cmip6-decadal.DCPP.MOHC.HadGEM3-GC31-MM.dcppA-hindcast.s1995-r5i1p1f2.Amon.tas.gn.v20200417",
    "c3s-cmip6-decadal.DCPP.MOHC.HadGEM3-GC31-MM.dcppA-hindcast.s1995-r6i1p1f2.Amon.tas.gn.v20200417",
    "c3s-cmip6-decadal.DCPP.MOHC.HadGEM3-GC31-MM.dcppA-hindcast.s1995-r7i1p1f2.Amon.tas.gn.v20200417",
    "c3s-cmip6-decadal.DCPP.MOHC.HadGEM3-GC31-MM.dcppA-hindcast.s1995-r8i1p1f2.Amon.tas.gn.v20200417",
    "c3s-cmip6-decadal.DCPP.MOHC.HadGEM3-GC31-MM.dcppA-hindcast.s1995-r9i1p1f2.Amon.tas.gn.v20200417",
    "c3s-cmip6-decadal.DCPP.MOHC.HadGEM3-GC31-MM.dcppA-hindcast.s1995-r10i1p1f2.Amon.tas.gn.v20200417",
)

C3S_CMIP6_DECADAL_CALENDAR_COLLECTIONS = (
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1976-r10i1p1f1.Amon.psl.gr.v20201216",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1976-r1i1p1f1.Amon.psl.gr.v20201215",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1976-r2i1p1f1.Amon.psl.gr.v20201215",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1976-r3i1p1f1.Amon.psl.gr.v20201215",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1976-r4i1p1f1.Amon.psl.gr.v20201216",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1976-r5i1p1f1.Amon.psl.gr.v20201216",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1976-r6i1p1f1.Amon.psl.gr.v20201216",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1976-r7i1p1f1.Amon.psl.gr.v20201216",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1976-r8i1p1f1.Amon.psl.gr.v20201216",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1976-r9i1p1f1.Amon.psl.gr.v20201216",  # noqa
)

C3S_CMIP6_DECADAL_DAY_COLLECTIONS = (
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1961-r10i1p1f1.day.psl.gr.v20201216",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1961-r1i1p1f1.day.psl.gr.v20201215",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1961-r2i1p1f1.day.psl.gr.v20201215",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1961-r3i1p1f1.day.psl.gr.v20201215",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1961-r4i1p1f1.day.psl.gr.v20201216",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1961-r5i1p1f1.day.psl.gr.v20201216",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1961-r6i1p1f1.day.psl.gr.v20201216",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1961-r7i1p1f1.day.psl.gr.v20201216",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1961-r8i1p1f1.day.psl.gr.v20201216",  # noqa
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1961-r9i1p1f1.day.psl.gr.v20201216",  # noqa
)

WF_C3S_CMIP5 = json.dumps(
    {
        "doc": "subset+average on cmip5",
        "inputs": {"ds": [C3S_CMIP5_DAY_COLLECTION]},
        "outputs": {"output": "average/output"},
        "steps": {
            "subset": {
                "run": "subset",
                "in": {"collection": "inputs/ds", "time": "2000/2000"},
            },
            "average": {
                "run": "average",
                "in": {"collection": "subset/output", "dims": "time"},
            },
        },
    }
)

WF_C3S_CMIP6 = json.dumps(
    {
        "doc": "subset+average on cmip6",
        "inputs": {"ds": [C3S_CMIP6_MON_COLLECTION]},
        "outputs": {"output": "average/output"},
        "steps": {
            "subset": {
                "run": "subset",
                "in": {"collection": "inputs/ds", "time": "2020-01-01/2020-12-31"},
            },
            "average": {
                "run": "average",
                "in": {"collection": "subset/output", "dims": "time"},
            },
        },
    }
)

WF_C3S_CMIP6_W_AVG = json.dumps(
    {
        "doc": "subset+weighted_average on cmip6",
        "inputs": {"ds": [C3S_CMIP6_MON_COLLECTION]},
        "outputs": {"output": "weighted_average/output"},
        "steps": {
            "subset": {
                "run": "subset",
                "in": {"collection": "inputs/ds", "time": "2020/2020"},
            },
            "weighted_average": {
                "run": "weighted_average",
                "in": {"collection": "subset/output"},
            },
        },
    }
)

WF_C3S_CMIP6_REGRID = json.dumps(
    {
        "doc": "subset+regrid on cmip6",
        "inputs": {"ds": [C3S_CMIP6_MON_COLLECTION]},
        "outputs": {"output": "regrid/output"},
        "steps": {
            "subset": {
                "run": "subset",
                "in": {"collection": "inputs/ds", "time": "2016/2016"},
            },
            "regrid": {
                "run": "regrid",
                "in": {
                    "collection": "subset/output",
                    "method": "nearest_s2d",
                    "grid": "1deg",
                },
            },
        },
    }
)

WF_C3S_CMIP6_REGRID_CUSTOM = json.dumps(
    {
        "doc": "subset+regrid on cmip6 with custom grid",
        "inputs": {"ds": [C3S_CMIP6_MON_COLLECTION]},
        "outputs": {"output": "regrid/output"},
        "steps": {
            "subset": {
                "run": "subset",
                "in": {"collection": "inputs/ds", "time": "2016/2016"},
            },
            "regrid": {
                "run": "regrid",
                "in": {
                    "collection": "subset/output",
                    "method": "nearest_s2d",
                    "grid": "custom",
                    "custom_grid": "0.5",
                },
            },
        },
    }
)

TC_ALL_DAYS = "day:01,02,03,04,05,06,07,08,09,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31"

WF_C3S_CMIP6_360DAY_CALENDAR = json.dumps(
    {
        "doc": "subset on cmip6",
        "inputs": {"ds": [C3S_CMIP6_360DAY_CALENDAR_COLLECTION]},
        "outputs": {"output": "subset/output"},
        "steps": {
            "subset": {
                "run": "subset",
                "in": {
                    "collection": "inputs/ds",
                    "time": "2015/2015",
                    "time_components": f"month:01,02,03|{TC_ALL_DAYS}",
                },
            },
        },
    }
)

WF_C3S_CMIP6_SUBSET_BATCHING = json.dumps(
    {
        "doc": "two-batch daily subset on cmip6",
        "inputs": {"huss": [C3S_CMIP6_DAY_HUSS_COLLECTION]},
        "outputs": {"output": "subset_huss_1/output"},
        "steps": {
            "subset_huss_1": {
                "run": "subset",
                "in": {
                    "collection": "inputs/huss",
                    "area": "25.5,35.5,45.0,42.5",
                    "time": "2015/2020",
                    "time_components": (
                        "month:jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,dec|"
                        "year:2015,2016,2017,2018,2019,2020"
                    ),
                },
            },
        },
    }
)

WF_C3S_CORDEX = json.dumps(
    {
        "doc": "subset on c3s-cordex",
        "inputs": {"ds": [C3S_CORDEX_DAY_COLLECTION]},
        "outputs": {"output": "average/output"},
        "steps": {
            "subset": {
                "run": "subset",
                "in": {
                    "collection": "inputs/ds",
                    "time": "2006/2006",
                    "time_components": "month:jan,feb,mar",
                },
            },
            "average": {
                "run": "average",
                "in": {"collection": "subset/output", "dims": "time"},
            },
        },
    }
)

WF_C3S_CORDEX_DAY_ALIGNED_SUBSET = json.dumps(
    {
        "doc": "return an aligned original file for a daily CORDEX subset",
        "inputs": {"ds": [C3S_CORDEX_DAY_COLLECTION]},
        "outputs": {"output": "subset/output"},
        "steps": {
            "subset": {
                "run": "subset",
                "in": {
                    "collection": "inputs/ds",
                    "time": "2006/2010",
                    "time_components": (
                        "year:2006,2007,2008,2009,2010|"
                        "month:jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,dec|"
                        f"{TC_ALL_DAYS}"
                    ),
                },
            },
        },
    }
)

WF_C3S_CMIP6_DECADAL = json.dumps(
    {
        "doc": "subset on c3s-cmip6-decadal",
        "inputs": {"ds": C3S_CMIP6_DECADAL_COLLECTIONS},
        "outputs": {"output": "subset/output"},
        "steps": {
            "concat": {
                "run": "concat",
                "in": {
                    "collection": "inputs/ds",
                    "dims": "realization",
                },
            },
            "average": {
                "run": "average",
                "in": {"collection": "concat/output", "dims": "realization"},
            },
            "subset": {
                "run": "subset",
                "in": {
                    "collection": "average/output",
                    "time": "1995/1995",
                },
            },
        },
    }
)


WF_C3S_CMIP6_DECADAL_2 = json.dumps(
    {
        "doc": "subset on c3s-cmip6-decadal with proleptic gregorian calendar",
        "inputs": {"ds": C3S_CMIP6_DECADAL_CALENDAR_COLLECTIONS},
        "outputs": {"output": "subset/output"},
        "steps": {
            "concat": {
                "run": "concat",
                "in": {
                    "collection": "inputs/ds",
                    "dims": "realization",
                    "time": "1985-01-01/1985-12-31",
                },
            },
            "subset": {
                "run": "subset",
                "in": {
                    "collection": "concat/output",
                    "time": "1985-01-01/1985-12-31",
                },
            },
        },
    }
)

WF_C3S_CMIP6_DECADAL_DAY_DECEMBER = json.dumps(
    {
        "doc": "December daily subset on c3s-cmip6-decadal",
        "inputs": {"psl": C3S_CMIP6_DECADAL_DAY_COLLECTIONS},
        "outputs": {"output": "subset_psl_1/output"},
        "steps": {
            "concat_psl_1": {
                "run": "concat",
                "in": {
                    "collection": "inputs/psl",
                    "dims": "realization",
                },
            },
            "subset_psl_1": {
                "run": "subset",
                "in": {
                    "collection": "concat_psl_1/output",
                    "time": "1962/1962",
                    "time_components": "month:dec|year:1962",
                    "area": "-10,30,35,70",
                },
            },
        },
    }
)


def concat_inputs(collections, time=None):
    inputs = [("collection", collection) for collection in collections]
    inputs.append(("dims", "realization"))
    if time is not None:
        inputs.append(("time", time))
    return inputs


def subset_inputs(collection, **params):
    inputs = [("collection", collection)]
    inputs.extend((name, value) for name, value in params.items() if value is not None)
    return inputs


def test_smoke_get_capabilities(wps):
    caps = wps.getcapabilities()
    assert caps.identification.type == "WPS"
    processes = [p.identifier for p in caps.processes]
    assert "subset" in processes
    assert "average" in processes
    assert "average_time" in processes
    assert "health" in processes
    assert "orchestrate" in processes


def test_smoke_nginx_health_get_capabilities(wps):
    response = requests.get(urljoin(wps.wps.url, "/health"), timeout=30)
    response.raise_for_status()

    caps = WebProcessingService(wps.wps.url, skip_caps=True)
    caps.getcapabilities(xml=response.content)

    assert caps.identification.type == "WPS"
    assert "health" in [process.identifier for process in caps.processes]


@pytest.mark.xfail(
    reason="Production access restrictions may block direct WPS execution; use the nginx /health2 endpoint instead."
)
def test_smoke_execute_health(wps):
    response = requests.get(
        wps.wps.url,
        params={
            "service": "WPS",
            "version": "1.0.0",
            "request": "Execute",
            "identifier": "health",
            "RawDataOutput": "status",
        },
        timeout=30,
    )

    response.raise_for_status()
    assert response.text == HEALTHY_RESPONSE


def test_smoke_nginx_health2_execute_health(wps):
    response = requests.get(urljoin(wps.wps.url, "/health2"), timeout=30)

    response.raise_for_status()
    assert response.text == HEALTHY_RESPONSE


def test_smoke_describe_process_subset(wps):
    process = wps.describeprocess("subset")
    assert process.identifier == "subset"
    inputs = [inp.identifier for inp in process.dataInputs]
    assert "collection" in inputs
    assert "time" in inputs
    assert "area" in inputs


def test_smoke_describe_process_average_dim(wps):
    process = wps.describeprocess("average")
    assert process.identifier == "average"
    inputs = [inp.identifier for inp in process.dataInputs]
    assert "collection" in inputs
    assert "dims" in inputs


def test_smoke_describe_process_average_time(wps):
    process = wps.describeprocess("average_time")
    assert process.identifier == "average_time"
    inputs = [inp.identifier for inp in process.dataInputs]
    assert "collection" in inputs
    assert "freq" in inputs


def test_smoke_describe_process_orchestrate(wps):
    process = wps.describeprocess("orchestrate")
    assert process.identifier == "orchestrate"
    inputs = [inp.identifier for inp in process.dataInputs]
    assert "workflow" in inputs


def test_smoke_execute_c3s_cmip5_subset(wps, tmp_path, open_dataset):
    inputs = [
        ("collection", C3S_CMIP5_DAY_COLLECTION),
        ("time", "2005-01-01/2005-12-31"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "tas_day_IPSL-CM5B-LR_historical_r1i1p1_20050101-20051231.nc" in urls[0]
    ds = open_dataset(urls[0], tmp_path)
    assert "tas" in ds.variables


def test_smoke_execute_c3s_cmip6_subset(wps, tmp_path, open_dataset):
    inputs = [
        ("collection", C3S_CMIP6_MON_COLLECTION),
        ("time", "2020-01-01/2020-12-30"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_20200116-20201216.nc" in urls[0]
    ds = open_dataset(urls[0], tmp_path)
    assert "rlds" in ds.variables


def test_smoke_execute_aligned_daily_subset_returns_original_file(wps):
    inputs = [
        ("collection", C3S_CMIP6_DAY_COLLECTION),
        ("time", "2015/2049"),
    ]
    urls = wps.execute("subset", inputs)

    assert len(urls) == 1
    assert "20150101-20491230" in urls[0]
    assert "esg_c3s-cmip6" in urls[0]


def test_smoke_execute_c3s_cmip6_subset_level(wps, tmp_path, open_dataset):
    inputs = [
        ("collection", C3S_CMIP6_MON_LEVEL_COLLECTION),
        ("time", "1850/1850"),
        ("time_components", "year:1850|month:jan"),
        ("level", "1000"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    ds = open_dataset(urls[0], tmp_path)
    assert "ta" in ds.variables


def test_smoke_execute_c3s_cmip6_subset_metadata(wps, tmp_path, open_dataset):
    inputs = [
        ("collection", C3S_CMIP6_MON_TASMIN_COLLECTION),
        ("time", "2010-01-01/2010-12-31"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert (
        "tasmin_Amon_MPI-ESM1-2-HR_historical_r1i1p1f1_gn_20100116-20101216.nc"
        in urls[0]
    )
    ds = open_dataset(urls[0], tmp_path)
    assert "tasmin" in ds.variables
    # check fill value in bounds
    assert "_FillValue" not in ds.lat_bnds.encoding
    assert "_FillValue" not in ds.lon_bnds.encoding
    assert "_FillValue" not in ds.time_bnds.encoding
    # check fill value in coordinates
    assert "_FillValue" not in ds.time.encoding
    assert "_FillValue" not in ds.lat.encoding
    assert "_FillValue" not in ds.lon.encoding
    assert "_FillValue" not in ds.height.encoding
    # check coordinates in bounds
    assert "coordinates" not in ds.lat_bnds.encoding
    assert "coordinates" not in ds.lon_bnds.encoding
    assert "coordinates" not in ds.time_bnds.encoding


def test_smoke_execute_c3s_cmip6_subset_area_fill_value(wps, tmp_path, open_dataset):
    dsid = "c3s-cmip6.CMIP.NCAR.CESM2-WACCM.historical.r1i1p1f1.day.tas.gn.v20190227"
    inputs = [
        ("collection", dsid),
        ("time", "2010-01-01/2010-12-30"),
        ("area", "5,49,7,51"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "tas_day_CESM2-WACCM_historical_r1i1p1f1_gn_20100101-20101230.nc" in urls[0]
    ds = open_dataset(urls[0], tmp_path)
    assert "tas" in ds.variables


def test_smoke_execute_c3s_cmip6_subset_noresm2_fix_282(wps, tmp_path, open_dataset):
    # TEST FOR ISSUE #282
    dsid = "c3s-cmip6.ScenarioMIP.NCC.NorESM2-MM.ssp245.r1i1p1f1.Omon.tos.gn.v20191108"
    inputs = [
        ("collection", dsid),
        ("time", "2049/2050"),
        ("time_components", "year:2049,2050|month:april"),
        ("area", "90,-180,-90,180"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "tos_Omon_NorESM2-MM_ssp245_r1i1p1f1_gn_20490416-20500416" in urls[0]
    ds = open_dataset(urls[0], tmp_path)
    assert "tos" in ds.variables


def test_smoke_execute_c3s_cordex_subset(wps, tmp_path, open_dataset):
    inputs = [
        ("collection", C3S_CORDEX_MON_COLLECTION),
        ("time", "2020-01-01/2020-12-30"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert (
        "tas_EUR-11_MOHC-HadGEM2-ES_rcp85_r1i1p1_CLMcom-CCLM4-8-17_v1_mon_20200116-20201216.nc"
        in urls[0]
    )
    assert "esg_c3s-cordex" not in urls[0]
    ds = open_dataset(urls[0], tmp_path)
    assert "tas" in ds.variables


def test_smoke_execute_c3s_cmip5_subset_by_point(wps, tmp_path, open_dataset):
    inputs = [
        ("collection", C3S_CMIP5_DAY_COLLECTION),
        ("time", "2005-01-01/2005-12-31"),
        ("time_components", "month:jan,feb,mar"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "tas_day_IPSL-CM5B-LR_historical_r1i1p1_20050101-20050331.nc" in urls[0]
    ds = open_dataset(urls[0], tmp_path)
    assert "tas" in ds.variables


def test_smoke_execute_c3s_cmip6_subset_by_point(wps, tmp_path, open_dataset):
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


def test_smoke_execute_c3s_cmip6_360calendar_subset_by_point(
    wps, tmp_path, open_dataset
):
    inputs = [
        ("collection", C3S_CMIP6_360DAY_CALENDAR_COLLECTION),
        ("time", "2015/2015"),
        ("time_components", f"month:jan,feb,mar|{TC_ALL_DAYS}"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "pr_day_HadGEM3-GC31-LL_ssp245_r1i1p1f3_gn_20150101-20150330.nc" in urls[0]
    ds = open_dataset(urls[0], tmp_path)
    assert "pr" in ds.variables


def test_smoke_execute_c3s_cordex_subset_by_point(wps, tmp_path, open_dataset):
    inputs = [
        ("collection", C3S_CORDEX_MON_COLLECTION),
        ("time", "2020-01-01/2020-12-30"),
        ("time_components", "month:jan,feb,mar"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert (
        "tas_EUR-11_MOHC-HadGEM2-ES_rcp85_r1i1p1_CLMcom-CCLM4-8-17_v1_mon_20200116-20200316.nc"
        in urls[0]
    )
    ds = open_dataset(urls[0], tmp_path)
    assert "tas" in ds.variables


def test_smoke_execute_c3s_cmip6_subset_original_files(wps):
    inputs = [
        ("collection", C3S_CMIP6_DAY_COLLECTION),
        ("time", "2020-01-01/2020-12-30"),
        ("original_files", "1"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "data.mips.climate.copernicus.eu" in urls[0]
    assert "esg_c3s-cmip6" in urls[0]


def test_smoke_execute_c3s_cmip6_subset_collection_only(wps):
    inputs = [("collection", C3S_CMIP6_DAY_COLLECTION)]
    urls = wps.execute("subset", inputs)
    print(urls)
    assert len(urls) == 2
    assert (
        "https://data.mips.climate.copernicus.eu/thredds/fileServer/esg_c3s-cmip6"
        in urls[0]
    )


def test_smoke_execute_c3s_cordex_subset_collection_only(wps):
    inputs = [("collection", C3S_CORDEX_MON_COLLECTION)]
    urls = wps.execute("subset", inputs)
    print(urls)
    assert len(urls) == 10
    assert "data.mips.climate.copernicus.eu" in urls[0]
    assert "esg_c3s-cordex" in urls[0]
    assert (
        "tas_EUR-11_MOHC-HadGEM2-ES_rcp85_r1i1p1_CLMcom-CCLM4-8-17_v1_mon_200601-201012.nc"
        in urls[0]
    )


def test_smoke_execute_c3s_cmip5_subset_time_and_area_cross_meridian(wps):
    inputs = [
        ("collection", C3S_CMIP5_MON_COLLECTION),
        ("time", "2005/2005"),
        ("area", "-50,-50,50,50"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "tas_mon_MPI-ESM-LR_historical_r1i1p1_20050116-20051216.nc" in urls[0]


def test_smoke_execute_c3s_cmip6_subset_time_and_area_cross_meridian(wps):
    inputs = [
        ("collection", C3S_CMIP6_MON_COLLECTION),
        ("time", "2020-01-01/2020-12-30"),
        ("area", "-50,-50,50,50"),
    ]
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_20200116-20201216.nc" in urls[0]


def test_smoke_execute_c3s_cmip5_average_dim(wps):
    inputs = [("collection", C3S_CMIP5_MON_COLLECTION), ("dims", "time")]
    urls = wps.execute("average", inputs)
    assert len(urls) == 1
    assert "tas_mon_MPI-ESM-LR_historical_r1i1p1_avg-t.nc" in urls[0]


def test_smoke_execute_c3s_cmip5_average_time(wps):
    inputs = [("collection", C3S_CMIP5_MON_COLLECTION), ("freq", "year")]
    urls = wps.execute("average_time", inputs)
    assert len(urls) == 1
    assert (
        "tas_mon_MPI-ESM-LR_historical_r1i1p1_18500101-20050101_avg-year.nc" in urls[0]
    )


def test_smoke_execute_c3s_cmip6_average_dim(wps):
    inputs = [("collection", C3S_CMIP6_MON_COLLECTION), ("dims", "time")]
    urls = wps.execute("average", inputs)
    assert len(urls) == 1
    assert "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_avg-t.nc" in urls[0]


def test_smoke_execute_c3s_cmip6_average_time(wps):
    inputs = [("collection", C3S_CMIP6_MON_COLLECTION), ("freq", "year")]
    urls = wps.execute("average_time", inputs)
    assert len(urls) == 1
    assert (
        "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_20150101-21000101_avg-year.nc"
        in urls[0]
    )


def test_smoke_execute_c3s_cordex_average_dim(wps):
    inputs = [("collection", C3S_CORDEX_MON_COLLECTION), ("dims", "time")]
    urls = wps.execute("average", inputs)
    # print(urls)
    assert len(urls) == 1
    assert (
        "tas_EUR-11_MOHC-HadGEM2-ES_rcp85_r1i1p1_CLMcom-CCLM4-8-17_v1_mon_avg-t.nc"
        in urls[0]
    )


def test_smoke_execute_c3s_cordex_average_time(wps):
    inputs = [("collection", C3S_CORDEX_MON_COLLECTION), ("freq", "year")]
    urls = wps.execute("average_time", inputs)
    # print(urls)
    assert len(urls) == 1
    assert (
        "tas_EUR-11_MOHC-HadGEM2-ES_rcp85_r1i1p1_CLMcom-CCLM4-8-17_v1_mon_20060101-20990101_avg-year.nc"
        in urls[0]
    )


def test_smoke_execute_c3s_cmip6_weighted_average(wps):
    inputs = [("collection", C3S_CMIP6_MON_COLLECTION)]
    urls = wps.execute("weighted_average", inputs)
    assert len(urls) == 1
    assert (
        "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_20150116-21001216_w-avg.nc" in urls[0]
    )


def test_smoke_execute_c3s_cmip6_regrid(wps):
    inputs = [
        ("collection", C3S_CMIP6_MON_COLLECTION),
        ("grid", "auto"),
        ("method", "nearest_s2d"),
    ]
    urls = wps.execute("regrid", inputs)
    assert len(urls) == 1
    assert (
        "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr_20150116-21001216_regrid-nearest_s2d-120x180_cells_grid.nc"
        in urls[0]
    )


def test_smoke_execute_c3s_cmip6_regrid_custom(wps):
    inputs = [
        ("collection", C3S_CMIP6_MON_COLLECTION),
        ("grid", "custom"),
        ("custom_grid", "0.5"),
        ("method", "nearest_s2d"),
    ]
    urls = wps.execute("regrid", inputs)
    assert len(urls) == 1
    assert (
        "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr_20150116-21001216_regrid-nearest_s2d-360x720_cells_grid.nc"
        in urls[0]
    )


def test_smoke_execute_c3s_cmip5_orchestrate(wps):
    inputs = [
        ("workflow", ComplexDataInput(WF_C3S_CMIP5)),
    ]
    urls = wps.execute("orchestrate", inputs)
    assert len(urls) == 1
    assert "tas_day_IPSL-CM5B-LR_historical_r1i1p1_avg-t.nc" in urls[0]


def test_smoke_execute_c3s_cmip6_orchestrate(wps):
    inputs = [
        ("workflow", ComplexDataInput(WF_C3S_CMIP6)),
    ]
    urls = wps.execute("orchestrate", inputs)
    assert len(urls) == 1
    assert "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_avg-t.nc" in urls[0]


def test_smoke_execute_c3s_cmip6_weighted_average_orchestrate(wps):
    inputs = [
        ("workflow", ComplexDataInput(WF_C3S_CMIP6_W_AVG)),
    ]
    urls = wps.execute("orchestrate", inputs)
    assert len(urls) == 1
    assert (
        "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_20200116-20201216_w-avg.nc" in urls[0]
    )


def test_smoke_execute_c3s_cmip6_regrid_orchestrate(wps):
    inputs = [
        ("workflow", ComplexDataInput(WF_C3S_CMIP6_REGRID)),
    ]
    urls = wps.execute("orchestrate", inputs)
    assert len(urls) == 1
    assert (
        "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr_20160116-20161216_regrid-nearest_s2d-180x360_cells_grid.nc"
        in urls[0]
    )


def test_smoke_execute_c3s_cmip6_regrid_custom_orchestrate(wps):
    inputs = [
        ("workflow", ComplexDataInput(WF_C3S_CMIP6_REGRID_CUSTOM)),
    ]
    urls = wps.execute("orchestrate", inputs)
    assert len(urls) == 1
    assert (
        "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr_20160116-20161216_regrid-nearest_s2d-360x720_cells_grid.nc"
        in urls[0]
    )


def test_smoke_execute_c3s_cmip6_360day_calendar_orchestrate(wps):
    inputs = [
        ("workflow", ComplexDataInput(WF_C3S_CMIP6_360DAY_CALENDAR)),
    ]
    urls = wps.execute("orchestrate", inputs)
    assert len(urls) == 1
    assert "pr_day_HadGEM3-GC31-LL_ssp245_r1i1p1f3_gn_20150101-20150330.nc" in urls[0]


def test_smoke_execute_c3s_cmip6_subset_batching_orchestrate(wps):
    inputs = [("workflow", ComplexDataInput(WF_C3S_CMIP6_SUBSET_BATCHING))]

    urls = wps.execute("orchestrate", inputs)

    assert len(urls) == 1
    assert "20150101-20201231" in urls[0]


def test_smoke_execute_c3s_cmip6_orchestrate_metadata(wps, tmp_path, open_dataset):
    inputs = [
        ("workflow", ComplexDataInput(WF_C3S_CMIP6)),
    ]
    urls = wps.execute("orchestrate", inputs)
    assert len(urls) == 1
    assert "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_avg-t.nc" in urls[0]
    ds = open_dataset(urls[0], tmp_path)
    assert "rlds" in ds.variables
    # check fill value in bounds
    assert "_FillValue" not in ds.lat_bnds.encoding
    assert "_FillValue" not in ds.lon_bnds.encoding
    # assert "_FillValue" not in ds.time_bnds.encoding
    # check fill value in coordinates
    # assert "_FillValue" not in ds.time.encoding
    assert "_FillValue" not in ds.lat.encoding
    assert "_FillValue" not in ds.lon.encoding
    # assert "_FillValue" not in ds.height.encoding
    # check coordinates in bounds
    assert "coordinates" not in ds.lat_bnds.encoding
    assert "coordinates" not in ds.lon_bnds.encoding
    # assert "coordinates" not in ds.time_bnds.encoding


def test_smoke_execute_c3s_cordex_orchestrate(wps):
    inputs = [
        ("workflow", ComplexDataInput(WF_C3S_CORDEX)),
    ]
    urls = wps.execute("orchestrate", inputs)
    assert len(urls) == 1
    assert (
        "tas_EUR-11_IPSL-IPSL-CM5A-MR_rcp85_r1i1p1_IPSL-WRF381P_v1_day_avg-t.nc"
        in urls[0]
    )


def test_smoke_execute_aligned_daily_cordex_subset_returns_original_file(wps):
    inputs = [
        ("workflow", ComplexDataInput(WF_C3S_CORDEX_DAY_ALIGNED_SUBSET)),
    ]
    urls = wps.execute("orchestrate", inputs)

    assert len(urls) == 1
    assert "20060101-20101231" in urls[0]
    assert "esg_c3s-cordex" in urls[0]


def test_smoke_execute_c3s_cmip6_decadal_concat(wps):
    inputs = concat_inputs(
        C3S_CMIP6_DECADAL_COLLECTIONS,
        time="1995/1995",
    )
    urls = wps.execute("concat", inputs)
    assert len(urls) == 1
    assert "tas_Amon_HadGEM3-GC31-MM_dcppA-hindcast" in urls[0]
    assert "19951116-19951216.nc" in urls[0]


def test_smoke_execute_c3s_cmip6_decadal_fix_calendar_concat(wps):
    inputs = concat_inputs(
        C3S_CMIP6_DECADAL_CALENDAR_COLLECTIONS,
        time="1985-01-01/1985-12-31",
    )
    urls = wps.execute("concat", inputs)
    assert len(urls) == 1
    assert "psl_Amon_EC-Earth3_dcppA-hindcast" in urls[0]
    assert "19850116-19851216.nc" in urls[0]


def test_smoke_execute_c3s_cmip6_decadal_daily_december_workflow(
    wps, tmp_path, open_dataset
):
    inputs = [
        ("workflow", ComplexDataInput(WF_C3S_CMIP6_DECADAL_DAY_DECEMBER)),
    ]

    urls = wps.execute("orchestrate", inputs)

    assert len(urls) == 1
    assert "psl_day_EC-Earth3_dcppA-hindcast" in urls[0]
    assert "19621201-19621231.nc" in urls[0]

    with open_dataset(urls[0], tmp_path) as dataset:
        assert dataset.sizes["realization"] == 10
        assert dataset.sizes["time"] == 31
        assert set(dataset.time.dt.year.values) == {1962}
        assert set(dataset.time.dt.month.values) == {12}
        assert dataset.lat.min() >= 30
        assert dataset.lat.max() <= 70
        assert dataset.lon.min() >= -10
        assert dataset.lon.max() <= 35


def test_smoke_execute_c3s_ipcc_atlas_cmip5_subset(wps):
    inputs = subset_inputs(C3S_IPCC_ATLAS_CMIP5_COLLECTION)
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "data.mips.climate.copernicus.eu" in urls[0]
    assert "esg_c3s-ipcc-atlas" in urls[0]
    assert "tnn_CMIP5_rcp45_mon_200601-210012.nc" in urls[0]


def test_smoke_execute_c3s_ipcc_atlas_cmip6_subset(wps):
    inputs = subset_inputs(C3S_IPCC_ATLAS_CMIP6_COLLECTION)
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "data.mips.climate.copernicus.eu" in urls[0]
    assert "esg_c3s-ipcc-atlas" in urls[0]
    assert "tnn_CMIP6_historical_mon_185001-201412.nc" in urls[0]


def test_smoke_execute_c3s_ipcc_atlas_cordex_subset(wps):
    inputs = subset_inputs(C3S_IPCC_ATLAS_CORDEX_COLLECTION)
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "data.mips.climate.copernicus.eu" in urls[0]
    assert "esg_c3s-ipcc-atlas" in urls[0]
    assert "tnn_CORDEX-AFR_historical_mon_197001-200512.nc" in urls[0]


def test_smoke_execute_c3s_cica_atlas_cmip6_subset(wps):
    inputs = subset_inputs(
        C3S_CICA_ATLAS_CMIP6_COLLECTION,
        time="2000/2000",
    )
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "data.mips.climate.copernicus.eu" not in urls[0]
    # assert "esg_c3s-cica-atlas" in urls[0]
    assert "cd_CMIP6_historical_yr_20000101-20000101.nc" in urls[0]


def test_smoke_execute_c3s_cica_atlas_cordex_subset(wps):
    inputs = subset_inputs(
        C3S_CICA_ATLAS_CORDEX_COLLECTION,
        time="2000/2000",
    )
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "data.mips.climate.copernicus.eu" not in urls[0]
    # assert "esg_c3s-cica-atlas" in urls[0]
    assert "cdd_CORDEX-CORE_historical_yr_20000101-20000101.nc" in urls[0]


def test_smoke_execute_c3s_cica_atlas_era5_subset_no_time_param(wps):
    inputs = subset_inputs(C3S_CICA_ATLAS_ERA5_COLLECTION)
    urls = wps.execute("subset", inputs)
    assert len(urls) == 1
    assert "data.mips.climate.copernicus.eu" in urls[0]
    assert "esg_c3s-cica-atlas" in urls[0]
    assert "cd_ERA5-Land_yr_1950-2025_v025.nc" in urls[0]
