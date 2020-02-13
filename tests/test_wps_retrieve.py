from pywps import Service
from pywps.tests import client_for, assert_response_success

from .common import get_output
from roocswps.processes.wps_retrieve import Retrieve


def test_wps_retrieve():
    client = client_for(Service(processes=[Retrieve()]))
    datainputs = "variable=geopotential_height"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=retrieve&datainputs={}".format(
            datainputs))
    assert_response_success(resp)
    assert 'output' in get_output(resp.xml)
