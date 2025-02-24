from pathlib import Path

import prov
import pytest
import xarray as xr
from pywps import Service
from pywps.tests import assert_response_success, client_for

from rook.processes.wps_orchestrate import Orchestrate
from rook.utils.metalink_utils import parse_metalink


def test_wps_orchestrate(resource_file, get_output, pywps_cfg):
    client = client_for(Service(processes=[Orchestrate()], cfgfiles=[pywps_cfg]))
    datainputs = "workflow=@xlink:href=file://{}".format(
        resource_file("wf_cmip6_subset_average.json")
    )
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=orchestrate&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]


def test_wps_orchestrate_subset_collection_only(resource_file, get_output, pywps_cfg):
    # TODO: this test is slow (25secs) ... but should be fast (1sec)
    client = client_for(Service(processes=[Orchestrate()], cfgfiles=[pywps_cfg]))
    datainputs = "workflow=@xlink:href=file://{}".format(
        resource_file("wf_c3s_cmip6_subset_collection_only.json")
    )
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=orchestrate&datainputs={datainputs}"
    )

    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]


def test_wps_orchestrate_prov(resource_file, get_output, pywps_cfg):
    client = client_for(Service(processes=[Orchestrate()], cfgfiles=[pywps_cfg]))
    datainputs = "workflow=@xlink:href=file://{}".format(
        resource_file("wf_cmip6_subset_average.json")
    )
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=orchestrate&datainputs={datainputs}"
    )
    assert_response_success(resp)
    file_uri = get_output(resp.xml)["prov"]
    doc = prov.read(file_uri[len("file://") :])
    assert 'roocs:time="1985-01-01/2014-12-30"' in doc.get_provn()
    assert 'roocs:freq="year"' in doc.get_provn()
    assert (
        "wasDerivedFrom(roocs:rlds_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_19850116-20141216.nc, roocs:CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.rlds.gr.v20180803"  # noqa
        in doc.get_provn()
    )
    assert (
        "wasDerivedFrom(roocs:rlds_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_19850101-20140101_avg-year.nc, roocs:rlds_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_19850116-20141216.nc"  # noqa
        in doc.get_provn()
    )


def test_wps_orchestrate_prov_with_fixes(resource_file, get_output, pywps_cfg):
    client = client_for(Service(processes=[Orchestrate()], cfgfiles=[pywps_cfg]))
    datainputs = "workflow=@xlink:href=file://{}".format(
        resource_file("wf_cmip6_subset_average_with_fixes.json")
    )
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=orchestrate&datainputs={datainputs}"
    )
    assert_response_success(resp)
    file_uri = get_output(resp.xml)["prov"]
    doc = prov.read(file_uri[len("file://") :])
    assert 'time="1985-01-01/2014-12-30"' in doc.get_provn()
    assert 'freq="year"' in doc.get_provn()


def test_wps_orchestrate_average_latlon_cmip6(resource_file, get_output, pywps_cfg):
    client = client_for(Service(processes=[Orchestrate()], cfgfiles=[pywps_cfg]))
    datainputs = "workflow=@xlink:href=file://{}".format(
        resource_file("wf_average_latlon_cmip6.json")
    )
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=orchestrate&datainputs={datainputs}"
    )
    assert_response_success(resp)
    file_uri = get_output(resp.xml)["prov"]
    doc = prov.read(file_uri[len("file://") :])
    assert 'time="1985-01-01/2014-12-30"' in doc.get_provn()
    assert 'dims="latitude,longitude"' in doc.get_provn()


@pytest.mark.xfail(reason="no cmip6 data in /pool/data")
def test_wps_orchestrate_c3s_cmip6_subset_metadata(
    resource_file, get_output, pywps_cfg
):
    client = client_for(Service(processes=[Orchestrate()], cfgfiles=[pywps_cfg]))
    datainputs = "workflow=@xlink:href=file://{}".format(
        resource_file("wf_c3s_cmip6_subset.json")
    )
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=orchestrate&datainputs={datainputs}"
    )
    assert_response_success(resp)
    m_path = get_output(resp.xml)["output"]
    # parse metalink
    xml = Path(m_path[7:]).open().read()
    urls = parse_metalink(xml)
    ds = xr.open_dataset(urls[0][7:], use_cftime=True)
    # check fill value in bounds
    assert "_FillValue" not in ds.lat_bnds.encoding
    assert "_FillValue" not in ds.lon_bnds.encoding
    assert "_FillValue" not in ds.time_bnds.encoding
    # check fill value in coordinates
    assert "_FillValue" not in ds.time.encoding
    assert "_FillValue" not in ds.lat.encoding
    assert "_FillValue" not in ds.lon.encoding
    assert "_FillValue" not in ds.height.encoding
    # check coordinates in bounds
    assert "coordinates" not in ds.lat_bnds.encoding
    assert "coordinates" not in ds.lon_bnds.encoding
    assert "coordinates" not in ds.time_bnds.encoding
