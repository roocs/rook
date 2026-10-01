import gzip
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pandas as pd
import pytest
from sqlalchemy import create_engine

from rook.dashboard import Dashboard
from rook.dashboard.plots import DownloadsPlot, TransferPlot
from rook.dashboard.tables import OverviewTable
from rook.usage import Combine, Downloads, WPSUsage
from rook.usage.combine import URLS, combine_csv, get_usage


@pytest.fixture
def usage_database(tmp_path, monkeypatch):
    rows = pd.DataFrame(
        {
            "uuid": ["success", "failure", "running", "other"],
            "pid": [1] * 4,
            "operation": ["execute", "execute", "execute", "getcapabilities"],
            "version": ["1.0.0"] * 4,
            "time_start": pd.to_datetime(
                [
                    "2021-06-08 00:00:00",
                    "2021-06-08 12:00:00.123456",
                    "2021-06-09 00:00:00",
                    "2021-06-08 00:00:00",
                ],
                format="mixed",
            ),
            "time_end": pd.to_datetime(
                [
                    "2021-06-08 00:00:10",
                    "2021-06-08 12:00:10.123456",
                    None,
                    "2021-06-08 00:00:10",
                ],
                format="mixed",
            ),
            "identifier": ["orchestrate"] * 4,
            "message": ["Done", 'Failed, with "quotes"\nand a newline', None, "Done"],
            "percent_done": [100.0, 100.0, 0.0, 100.0],
            "status": [4, 5, 1, 4],
        }
    )
    db_url = f"sqlite:///{tmp_path / 'pywps.db'}"
    engine = create_engine(db_url)
    rows.to_sql("pywps_requests", engine, index=False)
    engine.dispose()
    monkeypatch.setattr(
        "rook.usage.wpsusage.config",
        SimpleNamespace(get_config_value=lambda *args: db_url),
    )
    monkeypatch.setattr("rook.usage.wpsusage.CHUNK_SIZE", 1)
    return rows


@pytest.mark.parametrize(
    "start,end,expected_ids",
    [
        (None, None, ["success", "failure", "running"]),
        ("2021-06-08T12:00:00.123456", "2021-06-08T12:00:10.123456", ["failure"]),
        (None, "2021-06-08T00:00:10", ["success"]),
        ("2021-06-09", None, ["running"]),
        ("2022-01-01", None, []),
    ],
)
def test_database_export(tmp_path, usage_database, start, end, expected_ids):
    output = WPSUsage().collect(start, end, tmp_path)
    actual = pd.read_csv(output, parse_dates=["time_start", "time_end"])
    expected = usage_database.loc[usage_database.uuid.isin(expected_ids)].reset_index(
        drop=True
    )
    pd.testing.assert_frame_equal(actual, expected, check_dtype=False)


@pytest.mark.parametrize("empty", [False, True])
def test_combine_csv_chunks_and_columns(tmp_path, monkeypatch, empty):
    monkeypatch.setattr("rook.usage.combine.CHUNK_SIZE", 1)
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    a = pd.DataFrame({"uuid": ["001", "002"], "message": ['a, "quote"\nand ü', "NA"]})
    b = pd.DataFrame({"uuid": ["003"], "extra": ["new column"]})
    if empty:
        a, b = a.iloc[:0], b.iloc[:0]
    a.to_csv(first, index=False)
    b.to_csv(second, index=False)
    destination = tmp_path / "combined.csv"
    combine_csv([("ipsl", first), ("dkrz", second)], destination)
    a = a.assign(site="ipsl", URL=URLS["ipsl"])
    b = b.assign(site="dkrz", URL=URLS["dkrz"])
    expected = pd.concat([a, b], ignore_index=True).fillna("")
    actual = pd.read_csv(destination, dtype=str, keep_default_na=False)
    pd.testing.assert_frame_equal(actual, expected)


class BoundedResponse(BytesIO):
    def __init__(self, data, compressed=False):
        super().__init__(gzip.compress(data) if compressed else data)
        self.headers = {"Content-Encoding": "gzip"} if compressed else {}

    def read(self, size=-1):
        assert size > 0, "HTTP responses must not be read in full"
        return super().read(size)


def fake_wps(monkeypatch):
    response = SimpleNamespace(
        isComplete=lambda: True,
        isSucceded=lambda: True,
        processOutputs=[
            SimpleNamespace(
                identifier="downloads", reference="https://example.test/downloads"
            ),
            SimpleNamespace(
                identifier="wpsusage", reference="https://example.test/wpsusage"
            ),
        ],
    )
    service = MagicMock()
    service.execute.return_value = response
    monkeypatch.setattr(
        "rook.usage.combine.WebProcessingService", lambda **kwargs: service
    )
    return response


@pytest.mark.parametrize("site", ["local", "all"])
def test_usage_to_dashboard(tmp_path, monkeypatch, usage_database, resource_file, site):
    usage_csv = WPSUsage().collect(outdir=tmp_path)
    downloads_csv = Downloads().parse(
        [resource_file("access.log.txt")], outdir=tmp_path
    )
    payloads = {
        # Sites can use different timestamp precision; combining must retain
        # values that the dashboard can still parse together.
        "wpsusage": Path(usage_csv).read_bytes().replace(b".000000", b""),
        "downloads": Path(downloads_csv).read_bytes(),
    }
    fake_wps(monkeypatch)
    monkeypatch.setattr(
        "rook.usage.combine.urlopen",
        lambda url, **kwargs: BoundedResponse(
            payloads[url.rsplit("/", 1)[1]], compressed=True
        ),
    )
    monkeypatch.setattr("rook.usage.combine.CHUNK_SIZE", 1)
    combined_usage, combined_downloads = Combine(site).collect(outdir=tmp_path)
    assert not list(tmp_path.glob("usage-*")), "Temporary site files should be removed"
    multiplier = 2 if site == "all" else 1
    dash = Dashboard(output_dir=tmp_path)
    dash.load(combined_usage, filter="orchestrate")
    dash.load_downloads(combined_downloads)
    assert len(dash.df) == 2 * multiplier
    assert len(dash.df_downloads) == 4 * multiplier
    assert set(dash.df_downloads.columns) == {"datetime", "request_type", "size"}
    full_downloads = pd.read_csv(combined_downloads, parse_dates=["datetime"])
    expected_counts = full_downloads.groupby(
        pd.Grouper(key="datetime", freq="1D")
    ).request_type.count()
    pd.testing.assert_series_equal(
        DownloadsPlot(dash.df_downloads).data().request_type, expected_counts
    )
    expected_transfer = full_downloads["size"].sum() / 1024**3
    assert TransferPlot(dash.df_downloads).data()["size"].sum() == pytest.approx(
        expected_transfer
    )
    overview = OverviewTable(dash.df, dash.df_downloads).data()
    assert overview == OverviewTable(dash.df, full_downloads).data()
    values = dict(zip(overview["property"], overview["value"], strict=True))
    assert values["Total data transfer"] == f"{expected_transfer:.2f} GB"
    assert values["Total Requests"] == 2 * multiplier
    html = Path(dash.write()).read_text()
    assert "Overview" in html
    assert "Total data transfer" in html


def test_collection_failure_cleans_temporary_files(tmp_path, monkeypatch):
    fake_wps(monkeypatch)
    calls = []

    def download(url, **kwargs):
        calls.append(url)
        if len(calls) == 2:
            raise OSError("Download interrupted")
        return BoundedResponse(b"uuid\n001\n")

    monkeypatch.setattr("rook.usage.combine.urlopen", download)
    with pytest.raises(Exception, match="usage collection for site=local failed"):
        Combine("local").collect(outdir=tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_failed_wps_usage(tmp_path, monkeypatch):
    response = fake_wps(monkeypatch)
    response.isSucceded = lambda: False
    with pytest.raises(Exception, match="usage collection failed"):
        get_usage("local", "", tmp_path)
