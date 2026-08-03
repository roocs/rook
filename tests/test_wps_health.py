from pywps import Service
from pywps.tests import client_for

import rook.processes.wps_health as health_module
from rook.processes.wps_health import HEALTHY_RESPONSE, Health, HealthCheckError


def execute_health(client):
    return client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=health"
        "&RawDataOutput=status"
    )


def test_wps_health_returns_raw_success_marker():
    client = client_for(Service(processes=[Health()]))

    response = execute_health(client)

    assert response.status_code == 200
    assert response.content_type == "text/plain; charset=utf-8"
    assert response.data.decode() == HEALTHY_RESPONSE


def test_wps_health_explains_failed_check(monkeypatch):
    def fail_check():
        raise HealthCheckError("catalog database is unavailable")

    monkeypatch.setattr(health_module, "run_health_checks", fail_check)
    client = client_for(Service(processes=[Health()]))

    response = execute_health(client)

    assert response.status_code == 400
    assert HEALTHY_RESPONSE.encode() not in response.data
    assert b"Health check failed: catalog database is unavailable" in response.data
