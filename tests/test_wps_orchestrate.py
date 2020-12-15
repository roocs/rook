from pywps import Service
from pywps.tests import client_for, assert_response_success

from .common import get_output, resource_file, PYWPS_CFG
from rook.processes.wps_orchestrate import Orchestrate


def test_wps_orchestrate():
    client = client_for(Service(processes=[Orchestrate()], cfgfiles=[PYWPS_CFG]))
    datainputs = "workflow=@xlink:href=file://{0}".format(
        resource_file("subset_wf_1.json")
    )
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=orchestrate&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]
