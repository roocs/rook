import os
from pathlib import Path

import xarray as xr
import requests
import shutil

import pytest
from filelock import FileLock
from clisops.utils.testing import (
    ESGF_TEST_DATA_CACHE_DIR,
    ESGF_TEST_DATA_REPO_URL,
    ESGF_TEST_DATA_VERSION,
    load_registry,
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

TEST_DATA_FILE_PATTERNS = (
    "badc/cmip5/data/cmip5/output1/ICHEC/EC-EARTH/historical/mon/atmos/Amon/r1i1p1/latest/tas/",
    "badc/cmip5/data/cmip5/output1/MOHC/HadGEM2-ES/historical/mon/atmos/Amon/r1i1p1/latest/tas/",
    "badc/cmip6/data/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical/r1i1p1f1/Amon/rlds/gr/v20180803/",
    "badc/cmip6/data/CMIP6/CMIP/MPI-M/MPI-ESM1-2-HR/historical/r1i1p1f1/Amon/tasmin/gn/v20190710/",
    "badc/cmip6/data/CMIP6/CMIP/MPI-M/MPI-ESM1-2-HR/historical/r1i1p1f1/SImon/siconc/gn/",
    "badc/cmip6/data/CMIP6/DCPP/MOHC/HadGEM3-GC31-MM/",
    "badc/cmip6/data/CMIP6/ScenarioMIP/INM/INM-CM5-0/ssp245/r1i1p1f1/Amon/rlds/gr1/v20190619/",
    "badc/cmip6/data/CMIP6/ScenarioMIP/NCC/NorESM2-MM/",
    "gws/nopw/j04/cp4cds1_vol1/data/c3s-cmip5/output1/ICHEC/EC-EARTH/historical/day/atmos/day/r1i1p1/tas/v20131231/",
    "pool/data/c3s-cica-atlas/",
)


def required_test_data_files():
    registry = load_registry(
        branch=ESGF_TEST_DATA_VERSION,
        repo=ESGF_TEST_DATA_REPO_URL,
    )
    files = {
        filename
        for filename in registry
        if filename.startswith(TEST_DATA_FILE_PATTERNS)
    }
    return sorted(files)


def missing_test_data_files(base_dir):
    return [
        filename
        for filename in required_test_data_files()
        if not base_dir.joinpath(filename).exists()
    ]


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
    import clisops
    from rook.config import reload_config

    cfg = reload_config()
    clisops.CONFIG = cfg
    clisops.project_utils.CONFIG = cfg
    # print("clisops.config", clisops.CONFIG["project:cmip5"]["base_dir"])


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
def load_test_data(stratus, write_roocs_cfg):
    """Ensure that the required test data repository has been cloned to the cache directory within the home directory."""
    cache_dir = Path(ESGF_TEST_DATA_CACHE_DIR)
    marker = cache_dir.joinpath(ESGF_TEST_DATA_VERSION, ".rook_data_ready")
    lock = FileLock(cache_dir.joinpath(".rook_data.lock"))
    required_files = required_test_data_files()

    cache_dir.mkdir(exist_ok=True, parents=True)
    with lock:
        if marker.exists() and not missing_test_data_files(stratus.path):
            return

        failed_files = []
        for filename in required_files:
            try:
                stratus.fetch(filename)
            except requests.exceptions.HTTPError:
                failed_files.append(filename)

        missing_files = missing_test_data_files(stratus.path)
        if failed_files or missing_files:
            problem_files = sorted(set(failed_files + missing_files))
            raise RuntimeError(
                "Could not prepare required mini ESGF test data: "
                f"{problem_files}"
            )

        marker.parent.mkdir(exist_ok=True, parents=True)
        marker.touch()


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
