from pywps import Service
from pywps.tests import assert_process_exception, assert_response_success, client_for

from rook.processes.wps_average_dim import AverageByDimension


def test_wps_average_time_cmip5(get_output, pywps_cfg):
    client = client_for(Service(processes=[AverageByDimension()], cfgfiles=[pywps_cfg]))
    datainputs = "collection=c3s-cmip5.output1.ICHEC.EC-EARTH.historical.day.atmos.day.r1i1p1.tas.v20131231"
    datainputs += ";dims=time"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=average&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)


def test_wps_average_time_cmip6(get_output, pywps_cfg):
    # test the case where the inventory is used
    client = client_for(Service(processes=[AverageByDimension()], cfgfiles=[pywps_cfg]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    datainputs += ";dims=time"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=average&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)


def test_wps_average_latlon_cmip6(get_output, pywps_cfg):
    # test the case where the inventory is used
    client = client_for(Service(processes=[AverageByDimension()], cfgfiles=[pywps_cfg]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    datainputs += ";dims=latitude;dims=longitude"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=average&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)


def test_wps_average_no_dim(pywps_cfg):
    client = client_for(Service(processes=[AverageByDimension()], cfgfiles=[pywps_cfg]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=average&datainputs={datainputs}"
    )
    # print(resp.data)
    assert_process_exception(resp, code="MissingParameterValue")
