import gzip
from io import StringIO
from unittest.mock import MagicMock

import pandas as pd
import pytest

from rook.usage import Downloads
from rook.usage.downloads import NotFoundError, parse_record


def test_usage_downloads(tmpdir, resource_file):
    collector = Downloads()
    stats_csv = collector.parse(
        log_files=[resource_file("access.log.txt")], outdir=tmpdir
    )
    print(stats_csv)
    df = pd.read_csv(stats_csv)
    assert len(df) == 4


def test_downloads_plain_and_gzip(tmp_path, resource_file):
    source = resource_file("access.log.txt")
    compressed = tmp_path / "access.log.1.gz"
    with gzip.open(compressed, "wt") as stream:
        stream.write(source.read_text())
    collector = Downloads()
    result = collector.parse([source, compressed], outdir=tmp_path)
    actual = pd.read_csv(result, parse_dates=["datetime"], keep_default_na=False)
    records = [
        parse_record(line)
        for line in source.read_text().splitlines()
        if ".nc HTTP" in line
    ]
    expected_csv = StringIO(pd.DataFrame(records * 2).to_csv(index=False))
    expected = pd.read_csv(
        expected_csv, parse_dates=["datetime"], keep_default_na=False
    )
    pd.testing.assert_frame_equal(actual, expected)


@pytest.mark.parametrize(
    "start,end,count",
    [
        ("2021-06-08T16:19:10", "2021-06-08T16:21:51", 2),
        (None, "2021-06-08T16:19:10", 2),
        ("2021-06-08T16:21:51", None, 2),
        ("2022-01-01", None, 0),
    ],
)
def test_downloads_time_filter(tmp_path, resource_file, start, end, count):
    result = Downloads().parse([resource_file("access.log.txt")], start, end, tmp_path)
    df = pd.read_csv(result)
    assert len(df) == count
    assert "datetime" in df.columns


def test_downloads_skip_invalid_and_unmatched_logs(tmp_path, resource_file, caplog):
    caplog.set_level("WARNING")
    empty = tmp_path / "access.log.empty"
    empty.write_text("not a download\n")
    invalid = tmp_path / "access.log.invalid"
    invalid.write_text("invalid GET /outputs/rook/job/file.nc\n")
    result = Downloads().parse(
        [empty, invalid, resource_file("access.log.txt")], outdir=tmp_path
    )
    assert len(pd.read_csv(result)) == 4
    assert "Failed to process log file" not in caplog.text


@pytest.mark.parametrize(
    "contents", ["", "not a download\n", "GET /outputs/rook/job/file.nc\n"]
)
def test_downloads_no_records(tmp_path, contents):
    source = tmp_path / "access.log"
    source.write_text(contents)
    with pytest.raises(NotFoundError, match="Could not find any records"):
        Downloads().parse([source], outdir=tmp_path)


@pytest.mark.parametrize("returncodes", [(2, 0), (0, 2)])
def test_downloads_failed_log(
    tmp_path, resource_file, caplog, monkeypatch, returncodes
):
    caplog.set_level("ERROR")
    source = resource_file("access.log.txt")
    matches = "".join(
        line for line in source.read_text().splitlines(True) if ".nc HTTP" in line
    )
    processes = []
    for returncode in returncodes:
        process = MagicMock()
        process.stdout = StringIO(matches)
        process.returncode = returncode
        process.__enter__.return_value = process
        processes.append(process)
    monkeypatch.setattr(
        "rook.usage.downloads.subprocess.Popen", MagicMock(side_effect=processes)
    )
    result = Downloads().parse([source, source], outdir=tmp_path)
    assert len(pd.read_csv(result)) == 4
    assert "Failed to process log file" in caplog.text
