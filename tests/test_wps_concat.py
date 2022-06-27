import pytest

from pywps import Service
from pywps.tests import assert_process_exception, assert_response_success, client_for

from rook.processes.wps_concat import Concat

from .common import PYWPS_CFG, get_output


def test_wps_concat():
    client = client_for(Service(processes=[Concat()], cfgfiles=[PYWPS_CFG]))
    datainputs = """
    collections=c3s-cmip6-decadal.DCPP.DWD.MPI-ESM1-2-LR.dcppA-hindcast.s1980-r1i1p1f1.day.tasmax.gn.v20220126
    """
    request = "service=WPS&request=Execute&version=1.0.0&identifier=concat"
    resp = client.get(f"?{request}&datainputs={datainputs}")
    print(resp.data)
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)
