import pytest
from pywps.app import WPSRequest

from rook.utils.input_utils import (
    fix_time_components,
    parse_wps_input,
    resolve_to_file_paths,
)
from rook.utils.metalink_utils import build_metalink


def test_build_metalink(tmpdir, stratus):
    cmip6_nc = stratus.path.joinpath(
        "badc/cmip6/data/CMIP6/CMIP/MPI-M/MPI-ESM1-2-HR/historical/r1i1p1f1/SImon/siconc"
        "/gn/latest/siconc_SImon_MPI-ESM1-2-HR_historical_r1i1p1f1_gn_185001-185412.nc",
    ).as_posix()
    ml4 = build_metalink(
        "workflow-result",
        "Workflow result as NetCDF files.",
        tmpdir,
        [
            "https://data.mips.climate.copernicus.eu/thredds/fileServer/esg_c3s-cmip6"
            "/CMIP/NCC/NorESM1-F/piControl/r1i1p1f1/Amon/rsdt/gn/v20190920"
            "/rsdt_Amon_NorESM1-F_piControl_r1i1p1f1_gn_150101-151012.nc",  # noqa
            "http://data.mips.climate.copernicus.eu/thredds/fileServer/esg_c3s-cmip6"
            "/CMIP/NCC/NorESM1-F/piControl/r1i1p1f1/Amon/rsdt/gn/v20190920"
            "/rsdt_Amon_NorESM1-F_piControl_r1i1p1f1_gn_150101-151012.nc",  # noqa
            cmip6_nc,
        ],
    )
    assert "https://data.mips.climate.copernicus.eu" in ml4.files[0].url
    assert "http://data.mips.climate.copernicus.eu" in ml4.files[1].url
    assert "file://" in ml4.files[2].url


def test_resolve_to_file_paths_files():
    coll = [
        "/badc/cmip6/data/CMIP6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_200001-200912.nc",
        "/badc/cmip6/data/CMIP6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_201001-201412.nc",
    ]
    res = resolve_to_file_paths(coll)

    assert res == coll


def test_resolve_to_file_paths_mixed():
    coll = [
        "/badc/cmip6/data/CMIP6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_200001-200912.nc",
        "https://data.mips.climate.copernicus.eu/thredds/fileServer/esg_c3s-cmip6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_200001-200912.nc",
    ]

    with pytest.raises(Exception) as exc:
        resolve_to_file_paths(coll)
        assert (
            str(exc.value)
            == "Collections containing file paths and URLs are not accepted."
        )


def test_resolve_to_file_paths_urls(stratus):
    coll = [
        "https://data.mips.climate.copernicus.eu/thredds/fileServer/esg_c3s-cmip6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_200001-200912.nc",
        "https://data.mips.climate.copernicus.eu/thredds/fileServer/esg_c3s-cmip6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_201001-201412.nc",
    ]

    res = resolve_to_file_paths(coll)
    assert res == [
        f"{stratus.path}/pool/data/CMIP6/data/CMIP6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_200001-200912.nc",
        f"{stratus.path}/pool/data/CMIP6/data/CMIP6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_201001-201412.nc",
    ]


def test_parse_wps_input():
    obj = {
        "operation": "execute",
        "version": "1.0.0",
        "language": "eng",
        "identifier": "subset",
        "identifiers": "subset",  # TODO: why identifierS?
        "store_execute": True,
        "status": True,
        "lineage": True,
        "inputs": {
            "time": [
                {
                    "identifier": "time",
                    "type": "literal",
                    "data_type": "string",
                    "allowed_values": [{"type": "anyvalue"}],
                    "data": "1970/1980",
                }
            ],
            "time_components": [
                {
                    "identifier": "time",
                    "type": "literal",
                    "data_type": "string",
                    "allowed_values": [{"type": "anyvalue"}],
                    "data": "year:1970,1980|month=01,02,03",
                }
            ],
        },
        "outputs": {},
        "raw": False,
    }

    request = WPSRequest()
    request.json = obj

    assert parse_wps_input(request.inputs, "time", default=None) == "1970/1980"
    assert (
        parse_wps_input(request.inputs, "time_components", default=None)
        == "year:1970,1980|month=01,02,03"
    )


def test_fix_time_components():
    assert (
        fix_time_components("year:2000|month=01|day=01") == "year:2000|month=01|day=01"
    )

    all_days = "day:01,02,03,04,05,06,07,08,09,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31"
    assert (
        fix_time_components(f"year:2001,2002|month=02|{all_days}")
        == "year:2001,2002|month=02"
    )

    all_months = "month:jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,dec"
    assert (
        fix_time_components(f"year:2001,2002|{all_months}|{all_days}")
        == "year:2001,2002"
    )

    all_months_2 = "month:01,02,03,04,05,06,07,08,09,10,11,12"
    assert (
        fix_time_components(f"year:2001,2002|{all_months_2}|day:01,31")
        == "year:2001,2002|day:01,31"
    )

    assert fix_time_components("") is None
    assert fix_time_components(None) is None
