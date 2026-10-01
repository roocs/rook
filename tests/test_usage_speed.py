from datetime import datetime, timedelta

import pandas as pd
import pytest

from rook.dashboard.plots import ActivityPlot, DayPlot, DurationPlot
from rook.dashboard.plots.day import DAYS
from rook.usage.downloads import dot2longip, parse_record_time


def test_log_parser_caches_are_bounded():
    dot2longip.cache_clear()
    parse_record_time.cache_clear()
    try:
        start = datetime(2021, 1, 1)
        for i in range(5000):
            address = f"10.0.{i // 256}.{i % 256}"
            timestamp = start + timedelta(seconds=i)
            assert dot2longip(address) == 167772160 + i
            assert (
                parse_record_time(timestamp.strftime("%d/%b/%Y:%H:%M:%S")) == timestamp
            )
        for parser, value in (
            (dot2longip, address),
            (parse_record_time, timestamp.strftime("%d/%b/%Y:%H:%M:%S")),
        ):
            assert parser.cache_info().currsize == 4096
            hits = parser.cache_info().hits
            parser(value)
            assert parser.cache_info().hits == hits + 1
        with pytest.raises(ValueError):
            parse_record_time("31/Feb/2021:12:00:00")
        assert dot2longip("bad address") == 0
    finally:
        dot2longip.cache_clear()
        parse_record_time.cache_clear()


def test_vectorized_dashboard_statistics():
    start = pd.date_range("2021-06-01", periods=40, freq="12h")
    frame = pd.DataFrame(
        {
            "time_start": start,
            "time_end": start + pd.to_timedelta([0, 30, 60, 61, 86405] * 8, unit="s"),
            "status": [4, 5] * 20,
        }
    )
    expected = (
        pd.DataFrame(
            {
                "time": frame.time_start,
                "success": frame.status.apply(lambda value: 0 if value == 5 else 1),
                "failed": frame.status.apply(lambda value: 1 if value == 5 else 0),
            }
        )
        .groupby(pd.Grouper(key="time", freq="1D"))
        .sum()
        .sort_index(ascending=False)
    )
    pd.testing.assert_frame_equal(ActivityPlot(frame).data(), expected)
    expected_days = (
        frame.time_start.dt.dayofweek.apply(lambda value: DAYS[value])
        .value_counts()
        .sort_index()
    )
    actual_days = DayPlot(frame).data()
    assert list(actual_days["days"]) == list(expected_days.index)
    assert list(actual_days["counts"]) == list(expected_days.values)
    expected_duration = (frame.time_end - frame.time_start).dt.seconds.apply(
        lambda value: 60 if value > 60 else value
    )
    pd.testing.assert_series_equal(
        DurationPlot(frame).data().duration,
        expected_duration.rename("duration"),
        check_dtype=False,
    )
