from pywps import Service
from pywps.tests import assert_response_success, client_for

from rook.processes.wps_health import Health


def test_wps_health(get_output):
    client = client_for(Service(processes=[Health()]))

    response = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=health"
    )

    assert_response_success(response)
    assert get_output(response.xml)["status"] == "ok"
