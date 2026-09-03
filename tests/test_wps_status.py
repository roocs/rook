import json
from datetime import datetime, timedelta
from threading import Event
from types import SimpleNamespace

import pytest
from pywps import Service
from pywps.dblog import Base, ProcessInstance, RequestInstance
from pywps.response.status import WPS_STATUS
from pywps.tests import client_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import rook.processes.wps_status as wps_status_module
import rook.status.disk as disk_module
import rook.status.identification as identification_module
import rook.status.processes as processes_module
import rook.status.report as report_module
import rook.status.server as server_module
from rook.config import DEFAULT_STATUS
from rook.processes.wps_status import Status
from rook.status import collect_status, render_html
from rook.status.base import StatusCheck
from rook.status.disk import DiskStatusCheck
from rook.status.helpers import aggregate_state, make_check
from rook.status.identification import get_service_identification
from rook.status.processes import ProcessDatabaseStatusCheck
from rook.status.server import ServerStatusCheck

REPORT = {
    "schema_version": "1.0",
    "state": "yellow",
    "measured_at": "2026-09-03T10:00:00Z",
    "service": {
        "name": "rook",
        "version": "1.4.0",
        "provider": {"name": "rook7 (DKRZ)", "url": "http://rook.dkrz.de"},
        "contact": {
            "name": "DKRZ",
            "city": "Hamburg",
            "country": "Germany",
            "url": "https://roocs.github.io/",
        },
    },
    "checks": [
        {
            "id": "server",
            "state": "yellow",
            "message": "Server resources measured.",
            "measured_at": "2026-09-03T10:00:00Z",
            "details": {"cpu_percent": 82.5},
        }
    ],
}


def execute_status(client, output):
    return client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=status"
        f"&RawDataOutput={output}"
    )


def test_status_process_is_synchronous():
    process = Status()

    assert process.status_supported == "false"
    assert process.store_supported == "false"
    assert [output.identifier for output in process.outputs] == ["json", "html"]


def test_wps_status_returns_raw_json(monkeypatch):
    monkeypatch.setattr(wps_status_module, "collect_status", lambda: REPORT)
    client = client_for(Service(processes=[Status()]))

    response = execute_status(client, "json")

    assert response.status_code == 200
    assert response.content_type == "application/json"
    assert json.loads(response.data) == REPORT


def test_wps_status_returns_html_from_same_report(monkeypatch):
    monkeypatch.setattr(wps_status_module, "collect_status", lambda: REPORT)
    client = client_for(Service(processes=[Status()]))

    response = execute_status(client, "html")

    assert response.status_code == 200
    assert response.content_type == "text/html; charset=utf-8"
    assert b"Rook 1.4.0 status" in response.data
    assert b"rook7 (DKRZ)" in response.data
    assert b'href="https://roocs.github.io/"' in response.data
    assert b"cpu percent: 82.5" in response.data


def test_service_identification_uses_pywps_metadata(monkeypatch):
    metadata = {
        "provider_name": "rook7 (DKRZ)",
        "provider_url": "http://rook.dkrz.de",
        "contact_name": "DKRZ",
        "contact_city": "Hamburg",
        "contact_country": "Germany",
        "contact_url": "https://roocs.github.io/",
    }
    monkeypatch.setattr(
        identification_module.pywps_configuration,
        "get_config_value",
        lambda section, option: metadata[option],
    )

    assert get_service_identification() == {
        "provider": {
            "name": "rook7 (DKRZ)",
            "url": "http://rook.dkrz.de",
        },
        "contact": {
            "name": "DKRZ",
            "city": "Hamburg",
            "country": "Germany",
            "url": "https://roocs.github.io/",
        },
    }


def test_collect_status_preserves_results_when_a_check_fails(monkeypatch):
    monkeypatch.setattr(report_module, "get_status_config", lambda: DEFAULT_STATUS)

    class AvailableCheck(StatusCheck):
        identifier = "service"

        def collect(self, measured_at, _thresholds):
            return [make_check("service", "green", "Available.", measured_at)]

    class BrokenCheck(StatusCheck):
        identifier = "processes"

        def collect(self, _measured_at, _thresholds):
            raise RuntimeError("secret database location")

    report = collect_status([AvailableCheck(), BrokenCheck()])

    assert report["schema_version"] == "1.0"
    assert report["state"] == "red"
    assert report["checks"][0]["state"] == "green"
    assert report["checks"][1]["id"] == "processes"
    assert report["checks"][1]["state"] == "red"
    assert "secret database location" not in json.dumps(report)


def test_collect_status_marks_timeout_red_and_continues(monkeypatch):
    release = Event()
    config = {**DEFAULT_STATUS, "check_timeout_seconds": 0.01}
    monkeypatch.setattr(report_module, "get_status_config", lambda: config)

    class SlowCheck(StatusCheck):
        identifier = "slow"

        def collect(self, measured_at, _thresholds):
            release.wait()
            return [make_check(self.identifier, "green", "Late.", measured_at)]

    class AvailableCheck(StatusCheck):
        identifier = "available"

        def collect(self, measured_at, _thresholds):
            return [make_check(self.identifier, "green", "Available.", measured_at)]

    try:
        report = collect_status([SlowCheck(), AvailableCheck()])
    finally:
        release.set()

    assert report["state"] == "red"
    assert report["checks"][0] == {
        "id": "slow",
        "state": "red",
        "message": "Check timed out.",
        "measured_at": report["measured_at"],
        "details": {"timeout_seconds": 0.01},
    }
    assert report["checks"][1]["id"] == "available"
    assert report["checks"][1]["state"] == "green"


def test_state_aggregation_uses_most_severe_state():
    assert aggregate_state(["green", "yellow", "green"]) == "yellow"
    assert aggregate_state(["yellow", "red"]) == "red"


def test_process_check_counts_queue_active_stale_and_recent_results(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    now = datetime.now()
    with session_factory() as session:
        session.add_all(
            [
                _process("running", WPS_STATUS.STARTED, now - timedelta(minutes=5)),
                _process("stale", WPS_STATUS.STARTED, now - timedelta(hours=2)),
                _process("success", WPS_STATUS.SUCCEEDED, now - timedelta(minutes=4)),
                _process("failure", WPS_STATUS.FAILED, now - timedelta(minutes=3)),
                _process("status", WPS_STATUS.STARTED, now, identifier="status"),
                RequestInstance(uuid="queued", request=b"{}"),
            ]
        )
        session.commit()
    monkeypatch.setattr(processes_module, "get_session", session_factory)

    [check] = ProcessDatabaseStatusCheck().collect(
        "2026-09-03T10:00:00Z", {"stale_job_seconds": 3600}
    )

    assert check["state"] == "yellow"
    assert check["details"] == {
        "queued": 1,
        "running": 1,
        "stale": 1,
        "succeeded_24h": 1,
        "failed_24h": 1,
    }


def test_server_and_disk_checks_apply_thresholds(monkeypatch):
    monkeypatch.setattr(server_module.psutil, "cpu_count", lambda: 4)
    monkeypatch.setattr(
        server_module.psutil, "getloadavg", lambda: (3.6, 2.0, 1.0)
    )
    monkeypatch.setattr(server_module.psutil, "cpu_percent", lambda interval: 20.0)
    monkeypatch.setattr(
        server_module.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(percent=70.0, available=1_000_000),
    )
    monkeypatch.setattr(
        disk_module.psutil,
        "disk_usage",
        lambda path: SimpleNamespace(percent=96.0, free=10, total=100),
    )
    monkeypatch.setattr(
        disk_module.pywps_configuration,
        "get_config_value",
        lambda section, option: "/output",
    )

    [server] = ServerStatusCheck().collect(
        "2026-09-03T10:00:00Z", DEFAULT_STATUS
    )
    [disk] = DiskStatusCheck().collect("2026-09-03T10:00:00Z", DEFAULT_STATUS)

    assert server["state"] == "yellow"
    assert server["details"]["load_1m_percent"] == pytest.approx(90.0)
    assert disk["state"] == "red"


def test_html_renderer_escapes_public_values():
    report = {**REPORT, "checks": [{**REPORT["checks"][0], "message": "<script>"}]}

    rendered = render_html(report)

    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered


def test_html_renderer_does_not_link_unsafe_identification_url():
    report = {
        **REPORT,
        "service": {
            **REPORT["service"],
            "provider": {"name": "provider", "url": "javascript:alert(1)"},
        },
    }

    rendered = render_html(report)

    assert 'href="javascript:alert(1)"' not in rendered
    assert "javascript:alert(1)" in rendered


def _process(uuid, status, started, identifier="subset"):
    return ProcessInstance(
        uuid=uuid,
        pid=123,
        operation="execute",
        version="1.0.0",
        time_start=started,
        time_end=started + timedelta(seconds=30),
        identifier=identifier,
        percent_done=100 if status in (WPS_STATUS.SUCCEEDED, WPS_STATUS.FAILED) else 10,
        status=status,
    )
