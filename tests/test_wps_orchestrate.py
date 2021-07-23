import pytest

import prov

from pywps import Service
from pywps.tests import assert_response_success, client_for

from rook.processes.wps_orchestrate import Orchestrate

from .common import PYWPS_CFG, get_output, resource_file


def test_wps_orchestrate():
    client = client_for(Service(processes=[Orchestrate()], cfgfiles=[PYWPS_CFG]))
    datainputs = "workflow=@xlink:href=file://{}".format(
        resource_file("wf_cmip6_subset_average.json")
    )
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=orchestrate&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]


def test_wps_orchestrate_subset_collection_only():
    # TODO: this test is slow (25secs) ... but should be fast (1sec)
    client = client_for(Service(processes=[Orchestrate()], cfgfiles=[PYWPS_CFG]))
    datainputs = "workflow=@xlink:href=file://{}".format(
        resource_file("wf_c3s_cmip6_subset_collection_only.json")
    )
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=orchestrate&datainputs={}".format(
            datainputs
        )
    )

    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]


def test_wps_orchestrate_prov():
    client = client_for(Service(processes=[Orchestrate()], cfgfiles=[PYWPS_CFG]))
    datainputs = "workflow=@xlink:href=file://{}".format(
        resource_file("wf_cmip6_subset_average.json")
    )
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=orchestrate&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    file_uri = get_output(resp.xml)["prov"]
    print(file_uri)
    doc = prov.read(file_uri[len("file://") :])
    print(doc.get_provn())
    assert 'roocs:time="1985-01-01/2014-12-30"' in doc.get_provn()
    assert 'roocs:dims="time"' in doc.get_provn()
    assert (
        "wasDerivedFrom(roocs:rlds_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_19850116-20141216.nc, roocs:CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.rlds.gr.v20180803"  # noqa
        in doc.get_provn()
    )
    assert (
        "wasDerivedFrom(roocs:rlds_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_avg-t.nc, roocs:rlds_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_19850116-20141216.nc"  # noqa
        in doc.get_provn()
    )
    # assert "prov:startTime" in doc.get_provn()
    # assert "prov:endTime" in doc.get_provn()


def test_wps_orchestrate_prov_with_fixes():
    client = client_for(Service(processes=[Orchestrate()], cfgfiles=[PYWPS_CFG]))
    datainputs = "workflow=@xlink:href=file://{}".format(
        resource_file("wf_cmip6_subset_average_with_fixes.json")
    )
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=orchestrate&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    file_uri = get_output(resp.xml)["prov"]
    print(file_uri)
    doc = prov.read(file_uri[len("file://") :])
    print(doc.get_provn())
    assert 'time="1985-01-01/2014-12-30"' in doc.get_provn()
    assert 'dims="time"' in doc.get_provn()
