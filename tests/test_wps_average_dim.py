import pytest

from pywps import Service
from pywps.tests import assert_process_exception, assert_response_success, client_for

from rook.processes.wps_average_dim import AverageByDimension

from .common import PYWPS_CFG, get_output


def test_wps_average_time_cmip5():
    client = client_for(Service(processes=[AverageByDimension()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip5.output1.ICHEC.EC-EARTH.historical.day.atmos.day.r1i1p1.tas.latest"
    datainputs += ";dim=time"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=average_dim&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)


def test_wps_average_time_cmip6():
    # test the case where the inventory is used
    client = client_for(Service(processes=[AverageByDimension()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    datainputs += ";dim=time"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=average_dim&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)


def test_wps_average_latlon_cmip6():
    # test the case where the inventory is used
    client = client_for(Service(processes=[AverageByDimension()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    datainputs += ";dim=latitude;dim=longitude"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=average_dim&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)


def test_wps_average_no_dim():
    client = client_for(Service(processes=[AverageByDimension()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=average_dim&datainputs={datainputs}"
    )
    # print(resp.data)
    assert_process_exception(resp, code="MissingParameterValue")
