from pywps import Service
from pywps.tests import assert_response_success, client_for

from rook.processes.wps_average import Average

from .common import get_output


def test_wps_average_time():
    client = client_for(Service(processes=[Average()]))
    datainputs = "collection=c3s-cmip5.output1.ICHEC.EC-EARTH.historical.day.atmos.day.r1i1p1.tas.latest"
    datainputs += ";dims=time"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=average&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)


def test_wps_average_time_lat():
    client = client_for(Service(processes=[Average()]))
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
    client = client_for(Service(processes=[Average()]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    datainputs += ";dims=time,latitude"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=average&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)
