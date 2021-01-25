import os
import pytest

from rook.utils.input_utils import mapped_urls, resolve_input
from ..common import TESTS_HOME

test_dir = f"{TESTS_HOME}/mini-esgf-data/test_data"


def test_mapped_urls():
    coll = [
        "https://data.mips.copernicus-climate.eu/thredds/fileServer/esg_c3s-cmip6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_200001-200912.nc",
        "https://data.mips.copernicus-climate.eu/thredds/fileServer/esg_c3s-cmip6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_201001-201412.nc",
    ]
    dsets = mapped_urls(coll)
    assert dsets == [
        f"{test_dir}/badc/cmip6/data/CMIP6/CMIP/E3SM-Project/E3SM-1-1/historical/r1i1p1f1/Amon/rlus"
        f"/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_200001-200912.nc",
        f"{test_dir}/badc/cmip6/data/CMIP6/CMIP/E3SM-Project/E3SM-1-1/historical/r1i1p1f1/Amon/rlus"
        f"/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_201001-201412.nc",
    ]


@pytest.mark.skipif(os.path.isdir("/badc") is False, reason="data not available")
def test_resolve_input():
    coll = [
        "/badc/cmip6/data/CMIP6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_200001-200912.nc",
        "/badc/cmip6/data/CMIP6/CMIP/E3SM-Project/E3SM-1-1"
        "/historical/r1i1p1f1/Amon/rlus/gr/v20191211/rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_201001-201412.nc",
    ]
    res = resolve_input(coll)

    assert (
        res
        == "/badc/cmip6/data/CMIP6/CMIP/E3SM-Project/E3SM-1-1/historical/r1i1p1f1/Amon/rlus/gr/v20191211"
        "/{rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_200001-200912.nc,"
        "rlus_Amon_E3SM-1-1_historical_r1i1p1f1_gr_201001-201412.nc}"
    )
