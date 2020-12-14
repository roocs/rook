import glob
from rook.director.alignment import SubsetAlignmentChecker


class TestYearMonth:

    test_path = "tests/mini-esgf-data/test_data/badc/cmip5/data/cmip5/output1/MOHC/HadGEM2-ES/historical/mon/atmos/Amon" \
                "/r1i1p1/latest/tas/*.nc"
    test_paths = glob.glob(test_path)

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
        inputs = {"time": "1886-01-01/1984-11-01"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []

    def test_time_subset_match(self):
        inputs = {"time": "1859-12-01/2005-11-01"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == self.test_paths


class TestYearMonthDay:

    test_path = "tests/mini-esgf-data/test_data/group_workspaces/jasmin2/cp4cds1/vol1/data/c3s-cmip5/output1/ICHEC/" \
                "EC-EARTH/historical/day/atmos/day/r1i1p1/tas/v20131231/*.nc"
    test_paths = glob.glob(test_path)

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
        inputs = {"time": "1886-01-01/1900-01-01"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is False
        assert sac.aligned_files == []

    def test_time_subset_match(self):
        inputs = {"time": "1850-01-01/2009-11-30"}
        sac = SubsetAlignmentChecker(self.test_paths, inputs)
        assert sac.is_aligned is True
        assert sac.aligned_files == self.test_paths

