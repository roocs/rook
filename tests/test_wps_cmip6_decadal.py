import pytest

import xarray as xr

from pywps import Service
from pywps.tests import assert_process_exception, assert_response_success, client_for

from rook.processes.wps_subset import Subset

from .common import PYWPS_CFG, get_output, extract_paths_from_metalink


def assert_decadal_fix_applied(path):
    assert "meta4" in path
    paths = extract_paths_from_metalink(path)
    assert len(paths) > 0
    ds = xr.open_dataset(paths[0])
    assert "reftime" in ds.coords
    assert "leadtime" in ds.coords
    assert ds.leadtime.long_name == "Time elapsed since the start of the forecast"
    assert ds.leadtime.standard_name == "forecast_period"


@pytest.mark.xfail(reason="c3s-cmip6 decdal not in catalog")
def test_wps_subset_c3s_cmip6_decadal():
    client = client_for(Service(processes=[Subset()], cfgfiles=[PYWPS_CFG]))
    collection = "c3s-cmip6.DCPP.MOHC.HadGEM3-GC31-MM.dcppA-hindcast.s2004-r3i1p1f2.Amon.pr.gn.v20200417"
    datainputs = f"collection={collection}"
    # datainputs += ";time=1960-01-01/1961-01-01"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={}".format(
            datainputs
        )
    )
    assert_response_success(resp)
    assert_decadal_fix_applied(path=get_output(resp.xml)["output"])
