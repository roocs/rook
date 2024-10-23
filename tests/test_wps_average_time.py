from pathlib import Path

from pywps import Service
from pywps.tests import assert_process_exception, assert_response_success, client_for

from rook.processes.wps_average_time import AverageByTime

TESTS_HOME = Path(__file__).parent.absolute()
PYWPS_CFG = TESTS_HOME.joinpath("pywps.cfg")


def test_wps_average_year_cmip5(get_output):
    client = client_for(Service(processes=[AverageByTime()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip5.output1.ICHEC.EC-EARTH.historical.day.atmos.day.r1i1p1.tas.latest"
    datainputs += ";freq=year"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=average_time&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)


def test_wps_average_year_cmip6(get_output):
    # test the case where the inventory is used
    client = client_for(Service(processes=[AverageByTime()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    datainputs += ";freq=year"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=average_time&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)


def test_wps_average_no_freq():
    client = client_for(Service(processes=[AverageByTime()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=average_time&datainputs={datainputs}"
    )
    # print(resp.data)
    assert_process_exception(resp, code="MissingParameterValue")
