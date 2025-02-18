import pytest

from rook.director.alignment import SubsetAlignmentChecker


class TestYearMonth:
    """Tests with year and month only, not day"""

    test_path = "badc/cmip5/data/cmip5/output1/MOHC/HadGEM2-ES/historical/mon/atmos/Amon/r1i1p1/latest/tas/*.nc"

    @pytest.fixture
    def get_files(self, load_test_data, stratus):
        test_paths = sorted(stratus.path.glob(self.test_path))
        return test_paths

    # actual range in files is 185912-200511

    def test_no_subset(self, get_files):
        inputs = {}
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == get_files

    def test_area_subset(self, get_files):
        inputs = {"area": "0.,49.,10.,65"}
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []

    def test_time_subset_no_match(self, get_files):
        inputs = {"time": "1886-01/1930-11"}
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []

    def test_time_subset_one_match(self, get_files):
        inputs = {"time": "1886-01/1984-11"}
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []

    def test_time_subset_match(self, get_files):
        inputs = {"time": "1859-12/2005-11"}
        # start defaults to 1st of month
        # end defaults to 30th of month
        # the start and end day of dataset is 16th so this results in a requested time range outside of the actual range
        # so this is aligned.
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == get_files


class TestYearMonthDay1200:
    """Tests with year month and day for dataset with a 12:00:00 time step"""

    test_path = (
        f"gws/nopw/j04/cp4cds1_vol1/data/c3s-cmip5/output1/ICHEC/"
        f"EC-EARTH/historical/day/atmos/day/r1i1p1/tas/v20131231/*.nc"
    )
    # Actual range in files is: 18500101-20091130

    @pytest.fixture
    def get_files(self, load_test_data, stratus):
        test_paths = sorted(stratus.path.glob(self.test_path))
        return test_paths

    def test_no_subset(self, get_files):
        inputs = {}
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == get_files

    def test_area_subset(self, get_files):
        inputs = {"area": "0.,49.,10.,65"}
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []

    def test_time_subset_no_match(self, get_files):
        inputs = {"time": "1886-01-01/1930-11-01"}
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []

    def test_time_subset_one_match(self, get_files):
        inputs = {"time": "1900-01-01/1930-11-01"}
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []

    def test_time_subset_matches_one_file(self, get_files, stratus):
        inputs = {"time": "1900-01-01T12:00:00/1909-12-31T12:00:00"}
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files[0].as_posix() == (
            f"{stratus.path}/gws/nopw/j04/cp4cds1_vol1/data/c3s-cmip5"
            "/output1/ICHEC/EC-EARTH/historical/day/atmos/day/r1i1p1/tas/v20131231"
            "/tas_day_EC-EARTH_historical_r1i1p1_19000101-19091231.nc"
        )

    def test_time_subset_matches_exact_range_excluding_hour(self, get_files):
        """Tests alignment of full dataset where:
        - Real range: 18500101-20091130
        - Start: 18500101 (exact start)
        - End:   20091130 (exact end)
        """
        inputs = {"time": "1850-01-01/2009-11-30"}
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == get_files

    def test_time_subset_matches_before_to_end(self, get_files):
        """Tests alignment of full dataset where:
        - Real range: 18500101-20091130
        - Start: 17000101 (before)
        - End:   20091130T12:00:00 (exact end)
        """
        inputs = {"time": "1700-01-01/2009-11-30T12:00:00"}
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == get_files

    def test_time_subset_matches_start_to_after(self, get_files):
        """Tests alignment of full dataset where:
        - Real range: 18500101-20091130
        - Start: 18500101T12:00:00 (exact start)
        - End:   29991230 (after)
        """
        inputs = {"time": "1850-01-01T12:00:00/2999-12-30"}
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == get_files

    def test_time_subset_matches_before_to_after(self, get_files):
        """Tests alignment of full dataset where:
        - Real range: 18500101-20091130
        - Start: 17000101 (before)
        - End:   29991230 (after)
        """
        inputs = {"time": "1700-01-01/2999-12-30"}
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == get_files

    def test_time_subset_matches_including_hour(self, get_files):
        """Tests alignment of full dataset where:
        - Real range: 1850-01-01T12:00:00 to 2009-11-30T12:00:00
        - Start: 1850-01-01T12:00:00 (exact start)
        - End:   2009-11-30T12:00:00 (exact end)
        """
        inputs = {"time": "1850-01-01T12:00:00/2009-11-30T12:00:00"}
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == get_files

    def test_time_subset_no_match_including_hour(self, get_files):
        """Tests not aligned when time not aligned with file:
        - Real range: 1850-01-01T12:00:00 to 2009-11-30T12:00:00
        - Start: 1850-01-01T14:00:00 (start)
        - End:   2009-11-30T12:00:00 (exact end)
        """
        inputs = {"time": "1850-01-01T14:00:00/2009-11-30T12:00:00"}
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []


class TestYearMonthDay0000:
    """Tests with year month and day for dataset with a 00:00:00 time step"""

    test_path = f"badc/cmip5/data/cmip5/output1/MOHC/HadGEM2-ES/historical/mon/atmos/Amon/r1i1p1/latest/tas/*.nc"

    @pytest.fixture
    def get_files(self, load_test_data, stratus):
        test_paths = sorted(stratus.path.glob(self.test_path))
        return test_paths

    # actual range in files is 185912-200511

    def test_time_subset_matches_no_hour(self, get_files):
        """Tests alignment of full dataset where:
        - Real range: 1859-12-16T00:00:00 to 2005-11-16T00:00:00
        - Start: 1859-12-16 (start without hour)
        - End:   2005-11-16 (end without hour)

        """
        inputs = {"time": "1859-12-16/2005-11-16"}
        sac = SubsetAlignmentChecker(get_files, inputs)
        # aligns because default is timestamp of 00:00:00 if not provided
        assert sac.is_aligned is True
        assert sac.aligned_files == get_files

    def test_time_subset_matches_including_hour(self, get_files):
        """Tests alignment of full dataset where:
        - Real range: 1859-12-16T00:00:00 to 2005-11-16T00:00:00
        - Start: 1859-12-16T00:00:00 (exact start)
        - End:   2005-11-16T00:00:00 (exact end)
        """
        inputs = {"time": "1859-12-16T00:00:00/2005-11-16T00:00:00"}
        sac = SubsetAlignmentChecker(get_files, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == get_files
