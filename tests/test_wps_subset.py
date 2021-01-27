from pywps import Service
from pywps.tests import client_for, assert_response_success, assert_process_exception

from .common import get_output, PYWPS_CFG
from rook.processes.wps_subset import Subset


# Would expect this to raise an error
def test_wps_subset_no_inv():
    client = client_for(Service(processes=[Subset()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip5.output1.ICHEC.EC-EARTH.historical.day.atmos.day.r1i1p1.tas.latest"
    datainputs += ";time=1860-01-01/1900-12-30"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={}".format(
            datainputs
        )
    )
    assert resp.status_code == 200


def test_wps_subset_cmip6():
    client = client_for(Service(processes=[Subset()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.rlds.gr.v20180803"
    datainputs += ";time=1860-01-01/1900-12-30;area=1,1,300,89"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]


def test_wps_subset_cmip6_original_files():
    client = client_for(Service(processes=[Subset()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.rlds.gr.v20180803"
    datainputs += ";time=1860-01-01/1900-12-30;original_files=1"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]


def test_wps_subset_cmip6_collection_only():
    client = client_for(Service(processes=[Subset()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.rlds.gr.v20180803"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]


def test_wps_subset_missing_collection():
    client = client_for(Service(processes=[Subset()], cfgfiles=[PYWPS_CFG]))
    # datainputs = "collection=c3s-cmip5.output1.ICHEC.EC-EARTH.historical.day.atmos.day.r1i1p1.tas.latest"
    datainputs = ""
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={}".format(
            datainputs
        )
    )
    assert_process_exception(resp, code="MissingParameterValue")
