import prov

from pywps import Service
from pywps.tests import assert_process_exception, assert_response_success, client_for

from rook.processes.wps_subset import Subset

from .common import PYWPS_CFG, get_output


def test_wps_subset_cmip6_no_inv():
    client = client_for(Service(processes=[Subset()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.CMIP.MPI-M.MPI-ESM1-2-HR.historical.r1i1p1f1.SImon.siconc.gn.latest"
    datainputs += ";time=1860-01-01/1900-12-30"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={}".format(
            datainputs
        )
    )
    # assert resp.status_code == 200
    # print(resp.data)
    # assert_response_success(resp)
    assert (
        "Process error: Some or all of the requested collection are not in the list of available data"
        in str(resp.data)
    )


def test_wps_subset_cmip6():
    client = client_for(Service(processes=[Subset()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.rlds.gr.v20180803"
    datainputs += ";time=1860-01-01/1900-12-30;area=1,1,300,89"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]


def test_wps_subset_cmip6_prov():
    client = client_for(Service(processes=[Subset()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.rlds.gr.v20180803"
    datainputs += ";time=1860-01-01/1900-12-30;area=1,1,300,89"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    doc = prov.read(get_output(resp.xml)["prov"][len("file://"):])
    assert (
        'activity(subset, -, -, [time="1860-01-01/1900-12-30", area="1,1,300,89", apply_fixes="0" %% xsd:boolean])'
        in doc.get_provn()
    )
    assert (
        'wasDerivedFrom(rlds_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_18600116-19001216.nc, c3s-cmip6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.rlds.gr.v20180803, subset, -, -)'  # noqa
        in doc.get_provn()
    )


def test_wps_subset_cmip6_multiple_files_prov():
    client = client_for(Service(processes=[Subset()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=CMIP6.CMIP.MPI-M.MPI-ESM1-2-HR.historical.r1i1p1f1.SImon.siconc.gn.latest"
    datainputs += ";time=1850-01-01/2013-12-30"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    doc = prov.read(get_output(resp.xml)["prov"][len("file://"):])
    print(doc.get_provn())
    assert (
        'activity(subset, -, -, [time="1850-01-01/2013-12-30", apply_fixes="0" %% xsd:boolean])'
        in doc.get_provn()
    )
    assert (
        'wasDerivedFrom(siconc_SImon_MPI-ESM1-2-HR_historical_r1i1p1f1_gn_18500116-18960316.nc, CMIP6.CMIP.MPI-M.MPI-ESM1-2-HR.historical.r1i1p1f1.SImon.siconc.gn.latest, subset, -, -)'  # noqa
        in doc.get_provn()
    )
    assert (
        'wasDerivedFrom(siconc_SImon_MPI-ESM1-2-HR_historical_r1i1p1f1_gn_18960416-19420616.nc, CMIP6.CMIP.MPI-M.MPI-ESM1-2-HR.historical.r1i1p1f1.SImon.siconc.gn.latest, subset, -, -)'  # noqa
        in doc.get_provn()
    )


def test_wps_subset_cmip6_original_files():
    client = client_for(Service(processes=[Subset()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.rlds.gr.v20180803"
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


def test_wps_subset_time_invariant_dataset():
    client = client_for(Service(processes=[Subset()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.IPSL.IPSL-CM6A-LR.ssp119.r1i1p1f1.fx.mrsofc.gr.v20190410"
    datainputs += ";area=1,1,300,89"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    assert "meta4" in get_output(resp.xml)["output"]
