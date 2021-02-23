import os
import pytest

from rook.utils.input_utils import resolve_to_file_paths
from rook.utils.metalink_utils import build_metalink

from .common import TESTS_HOME, MINI_ESGF_MASTER_DIR

test_dir = f"{MINI_ESGF_MASTER_DIR}/test_data"


def test_build_metalink(tmpdir, load_test_data):
    cmip6_nc = os.path.join(
        test_dir,
        "badc/cmip6/data/CMIP6/CMIP/MPI-M/MPI-ESM1-2-HR/historical/r1i1p1f1/SImon/siconc"
        "/gn/latest/siconc_SImon_MPI-ESM1-2-HR_historical_r1i1p1f1_gn_185001-185412.nc",
    )  # noqa
    ml4 = build_metalink(
        "workflow-result",
        "Workflow result as NetCDF files.",
        tmpdir,
        [
            "https://data.mips.copernicus-climate.eu/thredds/fileServer/esg_c3s-cmip6"
            "/CMIP/NCC/NorESM1-F/piControl/r1i1p1f1/Amon/rsdt/gn/v20190920"
            "/rsdt_Amon_NorESM1-F_piControl_r1i1p1f1_gn_150101-151012.nc",  # noqa
            "http://data.mips.copernicus-climate.eu/thredds/fileServer/esg_c3s-cmip6"
            "/CMIP/NCC/NorESM1-F/piControl/r1i1p1f1/Amon/rsdt/gn/v20190920"
            "/rsdt_Amon_NorESM1-F_piControl_r1i1p1f1_gn_150101-151012.nc",  # noqa
            cmip6_nc,
        ],
    )
    assert "https://data.mips.copernicus-climate.eu" in ml4.files[0].url
    assert "http://data.mips.copernicus-climate.eu" in ml4.files[1].url
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
        "https://data.mips.copernicus-climate.eu/thredds/fileServer/esg_c3s-cmip6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_200001-200912.nc",
    ]

    with pytest.raises(Exception) as exc:
        resolve_to_file_paths(coll)
        assert (
            str(exc.value)
            == "Collections containing file paths and URLs are not accepted."
        )


def test_resolve_to_file_paths_urls(load_test_data):
    coll = [
        "https://data.mips.copernicus-climate.eu/thredds/fileServer/esg_c3s-cmip6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_200001-200912.nc",
        "https://data.mips.copernicus-climate.eu/thredds/fileServer/esg_c3s-cmip6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_201001-201412.nc",
    ]

    res = resolve_to_file_paths(coll)
    assert res == [
        f"{test_dir}/badc/cmip6/data/CMIP6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_200001-200912.nc",
        f"{test_dir}/badc/cmip6/data/CMIP6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_201001-201412.nc",
    ]
