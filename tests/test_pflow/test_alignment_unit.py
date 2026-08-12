from rook.pflow.alignment import SubsetAlignmentChecker


def test_long_three_hour_full_file_range_is_aligned(monkeypatch):
    input_files = [
        "cordex-1981-1990.nc",
        "cordex-1991-2000.nc",
        "cordex-2001-2010.nc",
    ]
    file_times = {
        input_files[0]: ("1981-01-01T00:00:00", "1990-12-31T21:00:00"),
        input_files[1]: ("1991-01-01T00:00:00", "2000-12-31T21:00:00"),
        input_files[2]: ("2001-01-01T00:00:00", "2010-12-31T21:00:00"),
    }
    monkeypatch.setattr(
        SubsetAlignmentChecker,
        "_get_file_times",
        lambda _self, path: file_times[path],
    )

    alignment = SubsetAlignmentChecker(
        input_files,
        {"time": "1981-01-01/2010-12-31"},
    )

    assert alignment.is_aligned is True
    assert alignment.aligned_files == input_files
