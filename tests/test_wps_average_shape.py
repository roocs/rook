from pathlib import Path

import geopandas as gpd
import xarray as xr
from pywps import Service
from pywps.tests import assert_process_exception, assert_response_success, client_for
from shapely import Polygon
from rook.utils.metalink_utils import parse_metalink

from rook.processes.wps_average_shape import AverageByShape

TESTS_HOME = Path(__file__).parent.absolute()
PYWPS_CFG = TESTS_HOME.joinpath("pywps.cfg")

POLY = Polygon(
    [
        [5.8671874999999996, 57.326521225217064],
        [-15.468749999999998, 48.45835188280866],
        [-16.171875, 24.84656534821976],
        [-3.8671874999999996, 13.581920900545844],
        [21.796875, 25.799891182088334],
        [22.8515625, 52.482780222078226],
        [5.8671874999999996, 57.326521225217064],
    ]
)


def test_wps_average_shape_cmip6(tmp_path, get_output):
    # Save POLY to tmpdir
    tmp_poly_path = tmp_path / "tmppoly.json"
    gpd.GeoDataFrame([{"geometry": POLY}]).to_file(tmp_poly_path.as_posix())

    # test the case where the inventory is used
    client = client_for(Service(processes=[AverageByShape()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    datainputs += f";shape={tmp_poly_path}"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=average_shape&datainputs={datainputs}"
    )
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)
    assert_geom_created(get_output(resp.xml)["output"])


def assert_geom_created(path):
    assert "meta4" in path
    paths = parse_metalink(path)
    assert len(paths) > 0
    ds = xr.open_dataset(paths[0])
    assert "geom" in ds.coords


def test_wps_average_no_shape():
    client = client_for(Service(processes=[AverageByShape()], cfgfiles=[PYWPS_CFG]))
    datainputs = "collection=c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    resp = client.get(
        f"?service=WPS&request=Execute&version=1.0.0&identifier=average_shape&datainputs={datainputs}"
    )
    assert_process_exception(resp, code="MissingParameterValue")
