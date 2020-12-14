from rook.director import Director
from pywps.app.exceptions import ProcessError
import pytest


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
        "CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.rlds.gr.v20180803"
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
        assert list(d.original_file_urls.items())[0][1] == ['https://data.mips.copernicus-climate.eu/thredds/fileServer'
                                                            '/esg_c3s-cmip6/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical'
                                                            '/r1i1p1f1/Amon/rlds/gr/v20180803/rlds_Amon_'
                                                            'IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc']

    def test_pre_checked_not_charactersied(self):
        # raise exception
        inputs = {"pre_checked": True}
        with pytest.raises(ProcessError):
            d = Director(self.collection, inputs)

    def apply_fixes_not_required(self):
        # no subset so original files
        inputs = {"apply_fixes": True}
        d = Director(self.collection, inputs)
        assert d.use_original_files is True
        assert list(d.original_file_urls.items())[0][1] == ['https://data.mips.copernicus-climate.eu/thredds/fileServer'
                                                            '/esg_c3s-cmip6/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical'
                                                            '/r1i1p1f1/Amon/rlds/gr/v20180803/rlds_Amon_'
                                                            'IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc']

    def test_area_or_level(self):
        # WPS output
        inputs = {"area": "0.,49.,10.,65"}
        d = Director(self.collection, inputs)
        assert d.use_original_files is False
    
    def test_time_subset_aligned(self):
        # original files
        inputs = {"time": "1850-01-01/2014-12-01"}
        d = Director(self.collection, inputs)
        assert d.use_original_files is True
        assert list(d.original_file_urls.items())[0][1] == ['https://data.mips.copernicus-climate.eu/thredds/fileServer'
                                                            '/esg_c3s-cmip6/CMIP6/CMIP/IPSL/IPSL-CM6A-LR/historical'
                                                            '/r1i1p1f1/Amon/rlds/gr/v20180803/rlds_Amon_'
                                                            'IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc']

    def test_only_time_no_match(self):
        inputs = {"time": "1900-03-12/2000-03-12"}
        d = Director(self.collection, inputs)
        assert d.use_original_files is False

# Any combinations ?


class TestDirector:

    collection = [
        "CMIP6.CMIP.NCAR.CESM2.amip.r3i1p1f1.Amon.cl.gn.v20190319"
    ]

    def test_not_in_inventory(self):
        # not in inventory
        inputs = {}
        with pytest.raises(ProcessError):
            Director(self.collection, inputs)


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
