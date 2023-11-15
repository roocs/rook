import pytest

from pywps import Service
from pywps.tests import assert_process_exception, assert_response_success, client_for

from rook.processes.wps_average_shape import AverageByShape

from .common import PYWPS_CFG, get_output


def test_wps_average_shape_cmip6():
    # test the case where the inventory is used
    client = client_for(Service(processes=[AverageByShape()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    datainputs += ";shape=not_a_valid_shape" #TODO figure out why this works without a valid shape
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=average_shape&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)


def test_wps_average_no_shape():
    client = client_for(Service(processes=[AverageByShape()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=average_shape&datainputs={datainputs}"
    )
    # print(resp.data)
    assert_process_exception(resp, code="MissingParameterValue")
