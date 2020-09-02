from pywps import Service
from pywps.tests import client_for, assert_response_success
import pytest

from .common import get_output, PYWPS_CFG
from rook.processes.wps_subset import Subset


def test_wps_subset():
    client = client_for(Service(processes=[Subset()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=cmip5.output1.MOHC.HadGEM2-ES.rcp85.mon.atmos.Amon.r1i1p1.latest.tas"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={}".format(
            datainputs))
    assert_response_success(resp)
    assert 'output' in get_output(resp.xml)
