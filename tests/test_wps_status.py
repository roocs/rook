import json
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from pywps import Service
from pywps.dblog import Base, ProcessInstance, RequestInstance
from pywps.response.status import WPS_STATUS
from pywps.tests import client_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import rook.processes.wps_status as wps_status_module
import rook.status as status_module
from rook.processes.wps_status import Status

REPORT = {
    "schema_version": "1.0",
    "state": "yellow",
    "measured_at": "2026-09-03T10:00:00Z",
    "service": {"name": "rook", "version": "1.4.0"},
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
    assert b"cpu percent: 82.5" in response.data


def test_collect_status_preserves_results_when_a_check_fails(monkeypatch):
    monkeypatch.setattr(
        status_module, "get_status_config", lambda: status_module.DEFAULT_STATUS
    )

    class AvailableCheck(status_module.StatusCheck):
        identifier = "service"

        def collect(self, measured_at, _thresholds):
            return [
                status_module._check("service", "green", "Available.", measured_at)
            ]

    class BrokenCheck(status_module.StatusCheck):
        identifier = "processes"

        def collect(self, _measured_at, _thresholds):
            raise RuntimeError("secret database location")

    report = status_module.collect_status([AvailableCheck(), BrokenCheck()])

    assert report["schema_version"] == "1.0"
    assert report["state"] == "red"
    assert report["checks"][0]["state"] == "green"
    assert report["checks"][1]["id"] == "processes"
    assert report["checks"][1]["state"] == "red"
    assert "secret database location" not in json.dumps(report)


def test_state_aggregation_uses_most_severe_state():
    assert status_module.aggregate_state(["green", "yellow", "green"]) == "yellow"
    assert status_module.aggregate_state(["yellow", "red"]) == "red"


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
    monkeypatch.setattr(status_module, "get_session", session_factory)

    [check] = status_module.ProcessDatabaseStatusCheck().collect(
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
    monkeypatch.setattr(status_module.psutil, "cpu_count", lambda: 4)
    monkeypatch.setattr(status_module.psutil, "getloadavg", lambda: (3.6, 2.0, 1.0))
    monkeypatch.setattr(status_module.psutil, "cpu_percent", lambda interval: 20.0)
    monkeypatch.setattr(
        status_module.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(percent=70.0, available=1_000_000),
    )
    monkeypatch.setattr(
        status_module.psutil,
        "disk_usage",
        lambda path: SimpleNamespace(percent=96.0, free=10, total=100),
    )
    monkeypatch.setattr(
        status_module.pywps_configuration,
        "get_config_value",
        lambda section, option: "/output",
    )

    [server] = status_module.ServerStatusCheck().collect(
        "2026-09-03T10:00:00Z", status_module.DEFAULT_STATUS
    )
    [disk] = status_module.DiskStatusCheck().collect(
        "2026-09-03T10:00:00Z", status_module.DEFAULT_STATUS
    )

    assert server["state"] == "yellow"
    assert server["details"]["load_1m_percent"] == pytest.approx(90.0)
    assert disk["state"] == "red"


def test_html_renderer_escapes_public_values():
    report = {**REPORT, "checks": [{**REPORT["checks"][0], "message": "<script>"}]}

    rendered = status_module.render_html(report)

    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered


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
