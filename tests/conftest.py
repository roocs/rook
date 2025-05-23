import os
from pathlib import Path

import xarray as xr
import requests
import shutil

import pytest
from clisops.utils.testing import (
    ESGF_TEST_DATA_CACHE_DIR,
    ESGF_TEST_DATA_REPO_URL,
    ESGF_TEST_DATA_VERSION,
    gather_testing_data,
)
from clisops.utils.testing import stratus as _stratus
from jinja2 import Template
from pywps import get_ElementMakerForVersion
from pywps.app.basic import get_xpath_ns
from pywps.tests import WpsClient, WpsTestResponse

VERSION = "1.0.0"
WPS, OWS = get_ElementMakerForVersion(VERSION)
xpath_ns = get_xpath_ns(VERSION)

TESTS_HOME = Path(__file__).parent.absolute()
ROOCS_CFG = TESTS_HOME.joinpath(".roocs.ini")
PYWPS_CFG = TESTS_HOME.joinpath("pywps.cfg")


@pytest.fixture(scope="session")
def stratus():
    return _stratus(
        repo=ESGF_TEST_DATA_REPO_URL,
        branch=ESGF_TEST_DATA_VERSION,
        cache_dir=ESGF_TEST_DATA_CACHE_DIR,
    )


@pytest.fixture(scope="session", autouse=True)
def write_roocs_cfg(stratus):
    cfg_templ = """
    [clisops:write]
    file_size_limit = 100KB

    [project:cmip5]
    base_dir = {{ base_dir }}/badc/cmip5/data/cmip5
    use_inventory = False

    [project:cmip6]
    base_dir = {{ base_dir }}/badc/cmip6/data/CMIP6
    use_inventory = False

    [project:cordex]
    base_dir = {{ base_dir }}/badc/cordex/data/cordex
    use_inventory = False

    [project:c3s-cmip5]
    base_dir = {{ base_dir }}/gws/nopw/j04/cp4cds1_vol1/data/c3s-cmip5

    [project:c3s-cmip6]
    base_dir = {{ base_dir }}/badc/cmip6/data/CMIP6

    [project:c3s-cmip6-decadal]
    base_dir = {{ base_dir }}/pool/data/CMIP6/data/CMIP6

    [project:c3s-cordex]
    base_dir = {{ base_dir }}/gws/nopw/j04/cp4cds1_vol1/data/c3s-cordex

    [project:c3s-cica-atlas]
    base_dir = {{ base_dir }}/pool/data/c3s-cica-atlas
    """  # noqa
    cfg = Template(cfg_templ).render(base_dir=stratus.path)
    with ROOCS_CFG.open("w") as fp:
        fp.write(cfg)
    # point to roocs cfg in environment
    os.environ["ROOCS_CONFIG"] = ROOCS_CFG.as_posix()
    # TODO: reload configs in clisops
    # workaround ... fix code in new clisops.
    import daops
    import clisops
    import rook

    cfg = daops.config_()
    clisops.CONFIG = cfg
    clisops.project_utils.CONFIG = cfg
    rook.CONFIG = cfg
    # rook.director.director.CONFIG = cfg
    # rook.catalog.CONFIG = cfg
    # print("clisops.config", clisops.CONFIG["project:cmip5"]["base_dir"])
    # print("rook.config", rook.CONFIG["project:cmip6"]["base_dir"])


@pytest.fixture
def pywps_cfg():
    return PYWPS_CFG


@pytest.fixture
def resource_file():
    def _resource_file(filename):
        return Path(TESTS_HOME).joinpath("testdata", filename)

    return _resource_file


@pytest.fixture
def fake_inv():
    os.environ["ROOK_FAKE_INVENTORY"] = "1"


class WpsTestClient(WpsClient):
    def get(self, *args, **kwargs):
        query = "?"
        for key, value in kwargs.items():
            query += f"{key}={value}&"
        return super().get(query)


@pytest.fixture
def client_for():

    def _client_for(service):
        return WpsTestClient(service, WpsTestResponse)

    return _client_for


@pytest.fixture
def get_output():
    """Return the WPS output. This method is copied from pywps/tests/test_execute.py."""

    def _get_output(doc):
        output = {}
        for output_el in xpath_ns(
            doc, "/wps:ExecuteResponse" "/wps:ProcessOutputs/wps:Output"
        ):
            [identifier_el] = xpath_ns(output_el, "./ows:Identifier")

            lit_el = xpath_ns(output_el, "./wps:Data/wps:LiteralData")
            if lit_el:
                output[identifier_el.text] = lit_el[0].text

            ref_el = xpath_ns(output_el, "./wps:Reference")
            if ref_el:
                output[identifier_el.text] = ref_el[0].attrib["href"]

            data_el = xpath_ns(output_el, "./wps:Data/wps:ComplexData")
            if data_el:
                output[identifier_el.text] = data_el[0].text

        return output

    return _get_output


@pytest.fixture(scope="session", autouse=True)
def load_test_data(stratus):
    """Ensure that the required test data repository has been cloned to the cache directory within the home directory."""
    repositories = {
        "stratus": {
            "worker_cache_dir": stratus.path,
            "repo": ESGF_TEST_DATA_REPO_URL,
            "branch": ESGF_TEST_DATA_VERSION,
            "cache_dir": ESGF_TEST_DATA_CACHE_DIR,
        },
    }

    for repo in repositories.values():
        gather_testing_data(worker_id="master", **repo)


def download_file(url, tmp_path):
    # use tmp_path (pathlib.Path) from pytest:
    # https://docs.pytest.org/en/stable/tmpdir.html
    local_filename = url.split("/")[-1]
    p = tmp_path / local_filename
    with requests.get(url, stream=True, timeout=30) as r:
        with p.open(mode="wb") as f:
            shutil.copyfileobj(r.raw, f)
    return p.as_posix()


@pytest.fixture
def open_dataset():
    def _open_dataset(url, tmp_path):
        ds = xr.open_dataset(download_file(url, tmp_path), use_cftime=True)
        return ds

    return _open_dataset
