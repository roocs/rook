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


def test_year_components_narrow_longer_time_to_original_files(monkeypatch):
    input_files = [f"huss-{year}.nc" for year in range(2015, 2021)]
    file_times = {
        path: (
            f"{year}-01-01T12:00:00",
            f"{year}-12-31T12:00:00",
        )
        for year, path in zip(range(2015, 2021), input_files)
    }
    monkeypatch.setattr(
        SubsetAlignmentChecker,
        "_get_file_times",
        lambda _self, path: file_times[path],
    )

    alignment = SubsetAlignmentChecker(
        input_files,
        {"time": "2015/2020", "time_components": "year:2015,2016"},
    )

    assert alignment.is_aligned is True
    assert alignment.aligned_files == input_files[:2]


def test_non_contiguous_years_still_require_subsetting(monkeypatch):
    input_files = [f"huss-{year}.nc" for year in range(2015, 2018)]
    file_times = {
        path: (
            f"{year}-01-01T12:00:00",
            f"{year}-12-31T12:00:00",
        )
        for year, path in zip(range(2015, 2018), input_files)
    }
    monkeypatch.setattr(
        SubsetAlignmentChecker,
        "_get_file_times",
        lambda _self, path: file_times[path],
    )

    alignment = SubsetAlignmentChecker(
        input_files,
        {"time": "2015/2017", "time_components": "year:2015,2017"},
    )

    assert alignment.is_aligned is False
    assert alignment.aligned_files == []


def test_partial_selected_year_still_requires_subsetting(monkeypatch):
    input_file = "huss-2015.nc"
    monkeypatch.setattr(
        SubsetAlignmentChecker,
        "_get_file_times",
        lambda _self, _path: (
            "2015-01-01T12:00:00",
            "2015-12-31T12:00:00",
        ),
    )

    alignment = SubsetAlignmentChecker(
        [input_file],
        {"time": "2015-06-01/2020", "time_components": "year:2015"},
    )

    assert alignment.is_aligned is False
    assert alignment.aligned_files == []
