import pytest

import xarray as xr
from bs4 import BeautifulSoup

from pywps import Service
from pywps.tests import assert_response_success, client_for

from rook.processes.wps_average_weighted import WeightedAverage

from .common import PYWPS_CFG, get_output


def extract_paths_from_metalink(path):
    path = path.replace("file://", "")
    doc = BeautifulSoup(open(path, "r").read(), "xml")
    paths = [el.text.replace("file://", "") for el in doc.find_all("metaurl")]
    return paths


def assert_weighted_average(path):
    assert "meta4" in path
    paths = extract_paths_from_metalink(path)
    assert len(paths) > 0
    print(paths)
    # ds = xr.open_dataset(paths[0])
    # assert "time" in ds.coords


def test_wps_weighted_average_cmip6():
    # test the case where the inventory is used
    client = client_for(Service(processes=[WeightedAverage()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=weighted_average&datainputs={datainputs}"
    )
    print(resp)
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)
    assert_weighted_average(path=get_output(resp.xml)["output"])
    assert False
