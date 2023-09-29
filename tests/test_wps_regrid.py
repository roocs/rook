import pytest

from pywps import Service
from pywps.tests import assert_response_success, client_for

from rook.processes.wps_regrid import Regrid

from .common import PYWPS_CFG, get_output


def test_wps_regrid_cmip6():
    client = client_for(Service(processes=[Regrid()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    datainputs += ";method=nearest_s2d"
    datainputs += ";grid=auto"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=regrid&datainputs={datainputs}"
    )
    print(resp)
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)
