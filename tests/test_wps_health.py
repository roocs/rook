import pytest
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


def test_health_checks_read_each_configured_file(monkeypatch, tmp_path):
    cmip6 = tmp_path / "cmip6" / ".health-check.txt"
    atlas = tmp_path / "atlas" / ".health-check.txt"
    cmip6.parent.mkdir()
    atlas.parent.mkdir()
    cmip6.write_bytes(b"healthy")
    atlas.write_bytes(b"healthy")
    monkeypatch.setattr(
        health_module,
        "get_health_readable_files",
        lambda: {"cmip6": str(cmip6), "atlas": str(atlas)},
    )

    health_module.run_health_checks()


def test_health_checks_report_names_without_exposing_paths(monkeypatch, tmp_path):
    missing_cmip6 = tmp_path / "private" / "cmip6.nc"
    missing_atlas = tmp_path / "private" / "atlas.nc"
    monkeypatch.setattr(
        health_module,
        "get_health_readable_files",
        lambda: {
            "cmip6": str(missing_cmip6),
            "atlas": str(missing_atlas),
        },
    )

    with pytest.raises(HealthCheckError) as exc_info:
        health_module.run_health_checks()

    message = str(exc_info.value)
    assert "cmip6: No such file or directory" in message
    assert "atlas: No such file or directory" in message
    assert str(tmp_path) not in message
