from pathlib import Path

import prov
import pytest
import xarray as xr
from pywps import Service
from pywps.tests import assert_process_exception, assert_response_success, client_for

from rook.processes.wps_subset import Subset
from rook.utils.metalink_utils import parse_metalink


C3S_CMIP6_MON_COLLECTION = (
    "c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
)

C3S_CMIP6_MON_TASMIN_COLLECTION = (
    "c3s-cmip6.CMIP.MPI-M.MPI-ESM1-2-HR.historical.r1i1p1f1.Amon.tasmin.gn.v20190710"
)

C3S_ATLAS_V2_CMIP5_COLLECTION = "c3s-cica-atlas.pr.CMIP5.rcp26.mon.v2"

C3S_ATLAS_V2_ERA5_COLLECTION = "c3s-cica-atlas.psl.ERA5.mon.v2"

C3S_ATLAS_V2_CORDEX_COLLECTION = "c3s-cica-atlas.huss.CORDEX-CORE.historical.mon.v2"


def test_wps_subset_cmip6_no_inv(pywps_cfg):
    client = client_for(Service(processes=[Subset()], cfgfiles=[pywps_cfg]))
    datainputs = "collection=c3s-cmip6.CMIP.MPI-M.MPI-ESM1-2-HR.historical.r1i1p1f1.SImon.siconc.gn.latest"
    datainputs += ";time=1860-01-01/1900-12-30"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={datainputs}"
    )
    assert (
        "Process error: Some or all of the requested collection are not in the list of available data"
        in str(resp.data)
    )


def test_wps_subset_c3s_cmip6(get_output, pywps_cfg):
    client = client_for(Service(processes=[Subset()], cfgfiles=[pywps_cfg]))
    datainputs = f"collection={C3S_CMIP6_MON_COLLECTION}"
    datainputs += ";time=2015-01-01/2015-12-30;area=1,1,300,89"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]


@pytest.mark.xfail(reason="no cmip6 data in /pool/data")
def test_wps_subset_c3s_cmip6_time_series(get_output, pywps_cfg):
    client = client_for(Service(processes=[Subset()], cfgfiles=[pywps_cfg]))
    datainputs = f"collection={C3S_CMIP6_MON_COLLECTION}"
    datainputs += ";time=2015-01-16T12:00:00,2016-01-16T12:00:00"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]


def test_wps_subset_c3s_cmip6_time_components(get_output, pywps_cfg):
    client = client_for(Service(processes=[Subset()], cfgfiles=[pywps_cfg]))
    datainputs = f"collection={C3S_CMIP6_MON_COLLECTION}"
    # datainputs += ";time=2015/2016"
    datainputs += ";time_components=year:2015,2016|month:01,02,03"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset&lineage=true&datainputs={datainputs}"
    )
    # print(resp.data)
    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]
    assert b"year:2015,2016|month:01,02,03" in resp.data


@pytest.mark.xfail(reason="no cmip6 data in /pool/data")
def test_wps_subset_c3s_cmip6_metadata(get_output, pywps_cfg):
    client = client_for(Service(processes=[Subset()], cfgfiles=[pywps_cfg]))
    datainputs = f"collection={C3S_CMIP6_MON_TASMIN_COLLECTION}"
    datainputs += ";time=2010/2010"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset&lineage=true&datainputs={datainputs}"
    )
    # print(resp.data)
    assert_response_success(resp)
    m_path = get_output(resp.xml)["output"]
    assert "meta4" in m_path
    # parse metalink
    xml = Path(m_path[7:]).open().read()
    urls = parse_metalink(xml)
    # print(urls)
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


def test_wps_subset_cmip6_prov(get_output, pywps_cfg):
    client = client_for(Service(processes=[Subset()], cfgfiles=[pywps_cfg]))
    datainputs = "collection=CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.rlds.gr.v20180803"
    datainputs += ";time=1860-01-01/1900-12-30;area=1,1,300,89"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={datainputs}"
    )
    assert_response_success(resp)
    doc = prov.read(get_output(resp.xml)["prov"][len("file://") :])
    assert (
        'roocs:time="1860-01-01/1900-12-30", roocs:area="1,1,300,89"' in doc.get_provn()
    )
    assert (
        "wasDerivedFrom(roocs:rlds_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_18600116-19001216.nc, roocs:CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.rlds.gr.v20180803"  # noqa
        in doc.get_provn()
    )


def test_wps_subset_cmip6_multiple_files_prov(get_output, pywps_cfg):
    client = client_for(Service(processes=[Subset()], cfgfiles=[pywps_cfg]))
    datainputs = "collection=CMIP6.CMIP.MPI-M.MPI-ESM1-2-HR.historical.r1i1p1f1.SImon.siconc.gn.latest"
    datainputs += ";time=1850-01-01/2013-12-30"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={datainputs}"
    )
    assert_response_success(resp)
    doc = prov.read(get_output(resp.xml)["prov"][len("file://") :])
    print(doc.get_provn())
    assert 'roocs:time="1850-01-01/2013-12-30"' in doc.get_provn()
    assert (
        "wasDerivedFrom(roocs:siconc_SImon_MPI-ESM1-2-HR_historical_r1i1p1f1_gn_18500116-20131216.nc, roocs:CMIP6.CMIP.MPI-M.MPI-ESM1-2-HR.historical.r1i1p1f1.SImon.siconc.gn.latest"  # noqa
        in doc.get_provn()
    )


def test_wps_subset_cmip6_original_files(get_output, pywps_cfg):
    client = client_for(Service(processes=[Subset()], cfgfiles=[pywps_cfg]))
    datainputs = "collection=CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.rlds.gr.v20180803"
    datainputs += ";time=1860-01-01/1900-12-30;original_files=1"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]


def test_wps_subset_c3s_cmip6_collection_only(get_output, pywps_cfg):
    client = client_for(Service(processes=[Subset()], cfgfiles=[pywps_cfg]))
    datainputs = f"collection={C3S_CMIP6_MON_COLLECTION}"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]


def test_wps_subset_missing_collection(pywps_cfg):
    client = client_for(Service(processes=[Subset()], cfgfiles=[pywps_cfg]))
    datainputs = ""
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={datainputs}"
    )
    assert_process_exception(resp, code="MissingParameterValue")


@pytest.mark.skip(reason="need a new test dataset")
def test_wps_subset_time_invariant_dataset(get_output, pywps_cfg):
    client = client_for(Service(processes=[Subset()], cfgfiles=[pywps_cfg]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.IPSL.IPSL-CM6A-LR.ssp119.r1i1p1f1.fx.mrsofc.gr.v20190410"
    datainputs += ";area=1,1,300,89"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]


@pytest.mark.xfail(reason="no atlas v2 data in /pool/data")
def test_wps_subset_c3s_atlas_v2_cmip5(get_output, pywps_cfg):
    client = client_for(Service(processes=[Subset()], cfgfiles=[pywps_cfg]))
    datainputs = f"collection={C3S_ATLAS_V2_CMIP5_COLLECTION}"
    datainputs += ";time=2020/2020"
    datainputs += ";time_components=month:jan,feb,mar"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]
    doc = prov.read(get_output(resp.xml)["prov"][len("file://") :])
    print(doc.get_provn())
    assert 'roocs:time="2020/2020"' in doc.get_provn()
    assert "roocs:pr_CMIP5_rcp26_mon_20200101-20200301.nc" in doc.get_provn()


@pytest.mark.xfail(reason="no atlas v2 data in /pool/data")
def test_wps_subset_c3s_atlas_v2_era5(get_output, pywps_cfg):
    client = client_for(Service(processes=[Subset()], cfgfiles=[pywps_cfg]))
    datainputs = f"collection={C3S_ATLAS_V2_ERA5_COLLECTION}"
    datainputs += ";time=2020/2020"
    datainputs += ";time_components=month:jan,feb,mar"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]
    doc = prov.read(get_output(resp.xml)["prov"][len("file://") :])
    print(doc.get_provn())
    assert 'roocs:time="2020/2020"' in doc.get_provn()
    assert "roocs:psl_ERA5_no-expt_mon_20200101-20200301.nc" in doc.get_provn()
