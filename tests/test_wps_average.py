from pywps import Service
from pywps.tests import client_for, assert_response_success

from .common import get_output
from rook.processes.wps_average import Average


def test_wps_average():
    client = client_for(Service(processes=[Average()]))
    datainputs = "data_ref=c3s-cmip5.output1.ICHEC.EC-EARTH.historical.day.atmos.day.r1i1p1.tas.latest"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=average&datainputs={}".format(
            datainputs))
    assert_response_success(resp)
    assert 'output' in get_output(resp.xml)
