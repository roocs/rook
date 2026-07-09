import os
from pathlib import Path

import pytest
import requests
from owslib.wps import WebProcessingService, monitorExecution
from owslib.util import ServiceException
from pywps import configuration as config

from rook.utils.metalink_utils import parse_metalink

TESTS_HOME = Path(__file__).parent.parent.absolute()
PYWPS_CFG = TESTS_HOME.joinpath("pywps.cfg")


def pytest_addoption(parser):
    parser.addoption(
        "--fix-provider",
        choices=("legacy", "woodpecker"),
        default="legacy",
        help=("Configured fix provider of the WPS instance under smoke test."),
    )


@pytest.fixture(params=("legacy", "woodpecker"))
def fix_provider(request, pytestconfig):
    """Return the selected smoke-test fix provider, skipping other providers."""
    selected_provider = pytestconfig.getoption("--fix-provider")
    provider = request.param
    if provider != selected_provider:
        pytest.skip(
            f"smoke test configured for {selected_provider!r} fix provider; "
            f"skipping {provider!r}"
        )
    return provider


def server_url():
    cfgfile = os.getenv("PYWPS_CFG", PYWPS_CFG.as_posix())
    config.load_configuration(cfgfiles=cfgfile)
    url = config.get_config_value("server", "url")
    return url


class RookWPS:
    def __init__(self, url):
        self.wps = WebProcessingService(url, skip_caps=True)

    def getcapabilities(self):
        self.wps.getcapabilities()
        return self.wps

    def describeprocess(self, identifier):
        return self.wps.describeprocess(identifier)

    def execute(self, identifier, inputs):
        outputs = [("output", True, None)]
        execution = self.wps.execute(identifier, inputs, output=outputs)
        monitorExecution(execution)
        print(execution.errors)
        assert execution.isSucceded() is True
        assert len(execution.processOutputs) > 0
        ml_url = execution.processOutputs[0].reference
        xml = requests.get(ml_url, timeout=30).text
        urls = parse_metalink(xml)
        return urls


@pytest.fixture
def wps():
    url = server_url()
    wps_ = RookWPS(url)
    try:
        wps_.getcapabilities()
    except (requests.RequestException, ServiceException) as exc:
        pytest.skip(f"WPS endpoint unavailable for smoke tests at {url}: {exc}")
    return wps_
