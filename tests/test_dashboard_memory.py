import pandas as pd
import pytest

from rook.dashboard import Dashboard
from rook.dashboard.models import daily_downloads
from rook.dashboard.plots import ConcurrencyPlot, DownloadsPlot, TransferPlot
from rook.dashboard.tables import MessageTable, OverviewTable


@pytest.mark.parametrize("chunk_size", [1, 2, 100])
def test_download_summary_preserves_statistics(tmp_path, monkeypatch, chunk_size):
    monkeypatch.setattr("rook.dashboard.dashboard.CHUNK_SIZE", chunk_size)
    downloads = pd.DataFrame(
        {
            "datetime": pd.to_datetime(
                [
                    "2021-06-04 12:00:00",
                    "2021-06-01 12:00:00",
                    None,
                    "2021-06-01 12:30:00",
                    "2021-06-04 00:00:00",
                ]
            ),
            "request_type": ["GET", "GET", "GET", None, "GET"],
            "size": [3 * 1024**3, 1024**3, 1000, None, 1024**3],
            "request": ["unused long request"] * 5,
        }
    )
    source = tmp_path / "downloads.csv"
    downloads.to_csv(source, index=False)
    dashboard = Dashboard(output_dir=tmp_path)
    dashboard.load_downloads(source)
    expected = downloads.groupby(pd.Grouper(key="datetime", freq="1D")).agg(
        download_count=("request_type", "count"), size=("size", "sum")
    )
    actual = daily_downloads(dashboard.df_downloads)
    pd.testing.assert_frame_equal(actual, expected, check_freq=False, check_dtype=False)
    assert actual.download_count.tolist() == [1, 0, 0, 2]
    assert actual["size"].sum() == 5 * 1024**3
    pd.testing.assert_frame_equal(
        DownloadsPlot(dashboard.df_downloads).data(),
        DownloadsPlot(downloads).data(),
        check_freq=False,
        check_dtype=False,
    )
    pd.testing.assert_frame_equal(
        TransferPlot(dashboard.df_downloads).data(),
        TransferPlot(downloads).data(),
        check_freq=False,
        check_dtype=False,
    )
    requests = pd.DataFrame(
        {
            "uuid": ["ok", "failed"],
            "status": [4, 5],
            "time_start": pd.to_datetime(["2021-06-01", "2021-06-02"]),
            "time_end": pd.to_datetime(["2021-06-01 00:00:10", "2021-06-02 00:00:20"]),
        }
    )
    assert (
        OverviewTable(requests, dashboard.df_downloads).data()
        == OverviewTable(requests, downloads).data()
    )


@pytest.mark.parametrize("rows", [0, 3])
def test_download_summary_without_dates(tmp_path, monkeypatch, rows):
    monkeypatch.setattr("rook.dashboard.dashboard.CHUNK_SIZE", 1)
    source = tmp_path / "downloads.csv"
    pd.DataFrame(
        {"datetime": [None] * rows, "request_type": ["GET"] * rows, "size": [10] * rows}
    ).to_csv(source, index=False)
    dashboard = Dashboard(output_dir=tmp_path)
    dashboard.load_downloads(source)
    assert dashboard.df_downloads.empty
    assert list(dashboard.df_downloads.columns) == [
        "datetime",
        "download_count",
        "size",
    ]


@pytest.mark.parametrize("filter_name", [None, "orchestrate", "missing"])
def test_request_loading_filters_chunks(tmp_path, monkeypatch, filter_name):
    monkeypatch.setattr("rook.dashboard.dashboard.CHUNK_SIZE", 1)
    requests = pd.DataFrame(
        {
            "uuid": ["later", "running", "earlier", "other"],
            "status": [4, 1, 5, 4],
            "time_start": pd.to_datetime(
                ["2021-06-03", "2021-06-02", "2021-06-01", "2021-06-02"]
            ),
            "time_end": pd.to_datetime(
                [
                    "2021-06-03 00:00:10",
                    None,
                    "2021-06-01 00:00:20",
                    "2021-06-02 00:00:05",
                ]
            ),
            "message": ["Done", "Running", "Failure", "Done"],
            "operation": ["execute", "execute", "execute", "getcapabilities"],
            "identifier": ["orchestrate"] * 4,
            "unused": ["large unused field"] * 4,
        }
    )
    path = tmp_path / "usage.csv"
    requests.to_csv(path, index=False)
    expected = requests[requests.status.isin([4, 5])]
    if filter_name:
        expected = expected[
            (expected.operation == "execute") & (expected.identifier == filter_name)
        ]
    expected = expected.sort_values("time_start")[
        ["uuid", "time_start", "time_end", "status", "message"]
    ]
    expected.loc[expected["status"] != 5, "message"] = None
    dashboard = Dashboard(output_dir=tmp_path)
    dashboard.load(path, filter=filter_name)
    pd.testing.assert_frame_equal(
        dashboard.df.reset_index(drop=True),
        expected.reset_index(drop=True),
        check_dtype=False,
    )
    if len(expected):
        pd.testing.assert_frame_equal(
            MessageTable(dashboard.df).data(),
            MessageTable(requests[requests.uuid.isin(dashboard.df.uuid)]).data(),
        )
        pd.testing.assert_frame_equal(
            ConcurrencyPlot(dashboard.df).data(), ConcurrencyPlot(expected).data()
        )


@pytest.mark.parametrize("timezone", [None, "UTC", "Europe/Berlin"])
@pytest.mark.parametrize("case", ["empty", "overlaps", "ties", "missing", "random"])
def test_compact_concurrency_matches_existing_metric(timezone, case):
    import numpy as np

    from rook.dashboard.models import concurrent_requests, daily_concurrency

    starts, ends = {
        "empty": ([], []),
        "overlaps": ([0, 1, 2, 4 * 86400], [10, 3, 6, 4 * 86400 + 30]),
        "ties": ([0, 0, 10, 10, 10], [10, 10, 10, 20, 30]),
        "missing": ([0, 1, 2, None], [10, None, 20, None]),
        "random": ([], []),
    }[case]
    if case == "random":
        rng = np.random.default_rng(123)
        starts = rng.integers(0, 5 * 86400, size=2000)
        ends = starts + rng.integers(0, 2 * 86400, size=2000)
    frame = pd.DataFrame(
        {
            "time_start": pd.Timestamp("2021-06-01")
            + pd.to_timedelta(starts, unit="s"),
            "time_end": pd.Timestamp("2021-06-01") + pd.to_timedelta(ends, unit="s"),
        }
    )
    if timezone:
        for column in frame:
            frame[column] = frame[column].dt.tz_localize(timezone)
    expected = (
        concurrent_requests(frame)
        .groupby(pd.Grouper(key="time", freq="1D"))
        .running.max()
    )
    pd.testing.assert_series_equal(daily_concurrency(frame), expected)
