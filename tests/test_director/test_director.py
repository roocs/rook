import pytest
from pywps.app.exceptions import ProcessError
from roocs_utils.exceptions import InvalidParameterValue

from rook.director import Director

# inputs = {"collection": None
#           "area": None,
#           "level": None,
#           "time": None,
#           "pre-checked": False,
#           "apply_fixes": False,
#           "original_files":False
#           }


class TestDirectorCMIP6:

    collection = [
        "c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
    ]

    def test_project(self):
        inputs = {}
        d = Director(self.collection, inputs)
        assert d.project == "c3s-cmip6"

    def test_original_files(self):
        # original files
        inputs = {"original_files": True}
        d = Director(self.collection, inputs)
        assert d.use_original_files is True
        assert list(d.original_file_urls.items())[0][1] == [
            "https://data.mips.copernicus-climate.eu/thredds/fileServer"
            "/esg_c3s-cmip6"
            "/ScenarioMIP/INM/INM-CM5-0/ssp245/r1i1p1f1/Amon/rlds/gr1/v20190619"
            "/rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_201501-210012.nc"
        ]

    def test_pre_checked_not_characterised(self):
        # raise exception
        inputs = {"pre_checked": True}
        with pytest.raises(ProcessError):
            Director(self.collection, inputs)

    def apply_fixes_not_required(self):
        # no subset so original files
        inputs = {"apply_fixes": True}
        d = Director(self.collection, inputs)
        assert d.use_original_files is True
        assert list(d.original_file_urls.items())[0][1] == [
            "https://data.mips.copernicus-climate.eu/thredds/fileServer"
            "/esg_c3s-cmip6/CMIP/IPSL/IPSL-CM6A-LR/historical"
            "/r1i1p1f1/Amon/rlds/gr/v20180803/rlds_Amon_"
            "IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc"
        ]

    def test_area_or_level(self):
        # WPS output
        inputs = {"area": "0.,49.,10.,65"}
        d = Director(self.collection, inputs)
        assert d.use_original_files is False

    def test_time_subset_aligned(self):
        # original files
        inputs = {"time": "2015-01-01/2100-12-31"}
        d = Director(self.collection, inputs)
        assert d.use_original_files is True
        assert list(d.original_file_urls.items())[0][1] == [
            "https://data.mips.copernicus-climate.eu/thredds/fileServer"
            "/esg_c3s-cmip6"
            "/ScenarioMIP/INM/INM-CM5-0/ssp245/r1i1p1f1/Amon/rlds/gr1/v20190619"
            "/rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_201501-210012.nc"
        ]

    def test_only_time_no_match(self):
        inputs = {"time": "1900-03-12/2000-03-12"}
        d = Director(self.collection, inputs)
        assert d.use_original_files is False


# Any combinations ?


class TestDirector:

    collection = ["CMIP6.CMIP.NCAR.CESM2.amip.r3i1p1f1.Amon.cl.gn.v20190319"]

    def test_no_inventory(self):
        # use_inventory for CMIP6 is set to False
        inputs = {"time": "1850-01-01/2014-12-01"}
        d = Director(self.collection, inputs)
        assert d.use_original_files is False
        assert d.original_file_urls is None
        assert d.output_uris is None


# need to test a  different dataset that has been characterised:

# def test_apply_fixes_required(self):
#     # wps output - can't test this with this dataset
#     inputs = {"apply_fixes": True}
#     pass
#     d = Director(self.collection, inputs)
#     assert d.use_original_files is False
#
#
# def test_pre_checked_charactersied(self):
#     # fine - can't test this with this dataset
#     inputs = {"pre_checked": True}
#     pass
#     d = Director(self.collection, inputs)
