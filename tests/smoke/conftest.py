from pathlib import Path

import pytest
import requests
from owslib.wps import WebProcessingService, monitorExecution
from pywps import configuration as config

from rook.utils.metalink_utils import parse_metalink

TESTS_HOME = Path(__file__).parent.parent.absolute()
PYWPS_CFG = TESTS_HOME.joinpath("pywps.cfg")


def server_url():
    config.load_configuration(cfgfiles=PYWPS_CFG.as_posix())
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
    wps_ = RookWPS(server_url())
    return wps_
