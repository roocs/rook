from pywps import Service
from pywps.tests import client_for, assert_response_success

from .common import get_output, resource_file
from roocswps.processes.wps_orchestrate import Orchestrate


def test_wps_orchestrate():
    client = client_for(Service(processes=[Orchestrate()]))
    datainputs = "workflow=@xlink:href=file://{0}".format(
        resource_file('subset-wf.json'))
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=orchestrate&datainputs={}".format(
            datainputs))
    assert_response_success(resp)
    assert 'output' in get_output(resp.xml)
