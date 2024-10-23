from pathlib import Path

import pytest
import xarray as xr
from pywps import Service
from pywps.tests import assert_response_success, client_for

from rook.processes.wps_regrid import Regrid

TESTS_HOME = Path(__file__).parent.absolute()
PYWPS_CFG = TESTS_HOME.joinpath("pywps.cfg")


@pytest.fixture
def assert_regrid(extract_paths_from_metalink):

    def _assert_regrid(path):
        assert "meta4" in path
        paths = extract_paths_from_metalink(path)
        assert len(paths) > 0
        ds = xr.open_dataset(paths[0])
        assert "time" in ds.coords

    return _assert_regrid


def test_wps_regrid_cmip6(assert_regrid, get_output):
    client = client_for(Service(processes=[Regrid()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.rlds.gr.v20180803"
    datainputs += ";method=nearest_s2d"
    datainputs += ";grid=auto"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=regrid&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)
    assert_regrid(path=get_output(resp.xml)["output"])
