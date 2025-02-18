from pathlib import Path

import pytest
import xarray as xr
from pywps import Service
from pywps.tests import assert_response_success, client_for

from rook.processes.wps_subset import Subset

TESTS_HOME = Path(__file__).parent.absolute()
PYWPS_CFG = TESTS_HOME.joinpath("pywps.cfg")


def assert_decadal_fix_applied(path, extract_paths_from_metalink):
    assert "meta4" in path
    paths = extract_paths_from_metalink(path)
    assert len(paths) > 0
    ds = xr.open_dataset(paths[0])
    assert "reftime" in ds.coords
    assert "leadtime" in ds.coords
    assert ds.leadtime.long_name == "Time elapsed since the start of the forecast"
    assert ds.leadtime.standard_name == "forecast_period"


@pytest.mark.xfail(reason="c3s-cmip6 decdal not in catalog")
def test_wps_subset_c3s_cmip6_decadal(get_output, extract_paths_from_metalink):
    client = client_for(Service(processes=[Subset()], cfgfiles=[PYWPS_CFG]))
    collection = "c3s-cmip6.DCPP.MOHC.HadGEM3-GC31-MM.dcppA-hindcast.s2004-r3i1p1f2.Amon.pr.gn.v20200417"
    datainputs = f"collection={collection}"
    # datainputs += ";time=1960-01-01/1961-01-01"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=subset&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert_decadal_fix_applied(
        get_output(resp.xml)["output"], extract_paths_from_metalink
    )
