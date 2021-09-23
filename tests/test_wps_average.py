import pytest

from pywps import Service
from pywps.tests import assert_process_exception, assert_response_success, client_for

from rook.processes.wps_average import Average

from .common import PYWPS_CFG, get_output


def test_wps_average_annual():
    client = client_for(Service(processes=[Average()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip5.output1.ICHEC.EC-EARTH.historical.day.atmos.day.r1i1p1.tas.latest"
    datainputs += ";aggregation=annual"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=average&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)


@pytest.mark.xfail(reason="adapt to new average")
def test_wps_average_time_lat():
    client = client_for(Service(processes=[Average()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip5.output1.ICHEC.EC-EARTH.historical.day.atmos.day.r1i1p1.tas.latest"
    datainputs += ";dims=time,latitude"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=average&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)


def test_wps_average_c3s_cmip6():
    # test the case where the inventory is used
    client = client_for(Service(processes=[Average()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    datainputs += ";aggregation=annual"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=average&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)


@pytest.mark.xfail(reason="adapt to new average")
def test_wps_average_dims_is_incorrect():
    client = client_for(Service(processes=[Average()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    datainputs += ";dims=banana"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=average&datainputs={}".format(
            datainputs
        )
    )
    assert (
        "Process error: Dimensions for averaging must be one of time , level , latitude , longitude"
        in str(resp.data)
    )


def test_wps_average_no_aggregation():
    client = client_for(Service(processes=[Average()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=average&datainputs={}".format(
            datainputs
        )
    )
    assert_process_exception(resp, code="MissingParameterValue")


@pytest.mark.xfail(reason="adapt to new average")
def test_wps_average_dims_is_empty_string():
    client = client_for(Service(processes=[Average()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    datainputs += ";dims="
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=average&datainputs={}".format(
            datainputs
        )
    )
    assert (
        "Process error: At least one dimension for averaging must be provided"
        in str(resp.data)
    )
