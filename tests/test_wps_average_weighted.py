import xarray as xr
from pywps import Service
from pywps.tests import assert_response_success, client_for

from rook.processes.wps_average_weighted import WeightedAverage
from rook.utils.metalink_utils import extract_paths_from_metalink


def assert_weighted_average(path):
    assert "meta4" in path
    paths = extract_paths_from_metalink(path)
    assert len(paths) > 0
    print(paths)
    ds = xr.open_dataset(paths[0])
    assert "time" in ds.coords


def test_wps_weighted_average_cmip6(get_output, pywps_cfg):
    # test the case where the inventory is used
    client = client_for(Service(processes=[WeightedAverage()], cfgfiles=[pywps_cfg]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=weighted_average&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)
    assert_weighted_average(get_output(resp.xml)["output"])
