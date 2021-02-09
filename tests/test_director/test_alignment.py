import glob
import os

import dateutil.parser as parser

from rook.director.alignment import SubsetAlignmentChecker


class TestYearMonth:
    """ Tests with year and month only, not day"""

    test_path = (
        "tests/mini-esgf-data/test_data/badc/cmip5/data/cmip5/output1/MOHC/HadGEM2-ES/historical/mon/atmos/Amon"
        "/r1i1p1/latest/tas/*.nc"
    )
    test_paths = sorted(glob.glob(test_path))

    # actual range in files is 185912-200511

    def test_no_subset(self):
        inputs = {}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == self.test_paths
        print(sac.aligned_files)
        print(self.test_paths)

    def test_area_subset(self):
        inputs = {"area": "0.,49.,10.,65"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []

    def test_time_subset_no_match(self):
        inputs = {"time": "1886-01/1930-11"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []

    def test_time_subset_one_match(self):
        inputs = {"time": "1886-01/1984-11"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []

    def test_time_subset_match(self):
        inputs = {"time": "1859-12/2005-11"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == self.test_paths


class TestYearMonthDay:
    """ Tests with year month and day """

    test_path = (
        "tests/mini-esgf-data/test_data/gws/nopw/j04/cp4cds1_vol1/data/c3s-cmip5/output1/ICHEC/"
        "EC-EARTH/historical/day/atmos/day/r1i1p1/tas/v20131231/*.nc"
    )
    # Actual range in files is: 18500101-20091130

    test_paths = sorted(glob.glob(test_path))

    def test_no_subset(self):
        inputs = {}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == self.test_paths

    def test_area_subset(self):
        inputs = {"area": "0.,49.,10.,65"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []

    def test_time_subset_no_match(self):
        inputs = {"time": "1886-01-01/1930-11-01"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []

    def test_time_subset_one_match(self):
        inputs = {"time": "1900-01-01/1930-11-01"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []

    def test_time_subset_matches_one_file(self):
        inputs = {"time": "1900-01-01T12:00:00/1909-12-31T12:00:00"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == [
            "tests/mini-esgf-data/test_data/gws/nopw/j04/cp4cds1_vol1/data/c3s-cmip5"
            "/output1/ICHEC/EC-EARTH/historical/day/atmos/day/r1i1p1/tas/v20131231"
            "/tas_day_EC-EARTH_historical_r1i1p1_19000101-19091231.nc"
        ]

    def test_time_subset_matches_exact_range_excluding_hour(self):
        """Tests alignment of full dataset where:
        - Real range: 18500101-20091130
        - Start: 18500101 (exact start)
        - End:   20091130 (exact end)

        Is not aligned as the hour is set to 00:00:00 when not provided and the time stamp
        for these files is 12:00:00.
        """
        inputs = {"time": "1850-01-01/2009-11-30"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []

    def test_time_subset_matches_before_to_end(self):
        """Tests alignment of full dataset where:
        - Real range: 18500101-20091130
        - Start: 17000101 (before)
        - End:   20091130T12:00:00 (exact end)
        """
        inputs = {"time": "1700-01-01/2009-11-30T12:00:00"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == self.test_paths

    def test_time_subset_matches_start_to_after(self):
        """Tests alignment of full dataset where:
        - Real range: 18500101-20091130
        - Start: 18500101T12:00:00 (exact start)
        - End:   29991230 (after)
        """
        inputs = {"time": "1850-01-01T12:00:00/2999-12-30"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == self.test_paths

    def test_time_subset_matches_before_to_after(self):
        """Tests alignment of full dataset where:
        - Real range: 18500101-20091130
        - Start: 17000101 (before)
        - End:   29991230 (after)
        """
        inputs = {"time": "1700-01-01/2999-12-30"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == self.test_paths

    def test_time_subset_matches_including_hour(self):
        """Tests alignment of full dataset where:
        - Real range: 1850-01-01T12:00:00 to 2009-11-30T12:00:00
        - Start: 1850-01-01T12:00:00 (exact start)
        - End:   2009-11-30T12:00:00 (exact end)
        """
        inputs = {"time": "1850-01-01T12:00:00/2009-11-30T12:00:00"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == self.test_paths

    def test_time_subset_no_match_including_hour(self):
        """Tests not aligned when time not aligned with file:
        - Real range: 1850-01-01T12:00:00 to 2009-11-30T12:00:00
        - Start: 1850-01-01T14:00:00 (start)
        - End:   2009-11-30T12:00:00 (exact end)
        """
        inputs = {"time": "1850-01-01T14:00:00/2009-11-30T12:00:00"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []


# def dummy_time_parse(fpath):
#     start, end = os.path.basename(fpath).split(".")[-2].split("_")[-1].split("-")
#     start, end = [
#         each[:6] + "01" + each[6:] if len(each) == 6 else each for each in (start, end)
#     ]
#     start, end = [
#         each[:8] + "T" + each[8:] if len(each) > 8 else each for each in (start, end)
#     ]
#     start, end = (
#         parser.isoparse(start).isoformat(),
#         parser.isoparse(end).isoformat(),
#     )
#     return start, end
#
#
# def test_parse_YMDhm():
#     fpath = (
#         "ScenarioMIP/AWI/AWI-CM-1-1-MR/ssp245/r1i1p1f1/3hr/tas/gn/v20190529"
#         "/tas_3hr_AWI-CM-1-1-MR_ssp245_r1i1p1f1_gn_207301010300-207401010000.nc"
#     )
#     start, end = dummy_time_parse(fpath)
#     assert start == "2073-01-01T03:00:00"
#     assert end == "2074-01-01T00:00:00"
