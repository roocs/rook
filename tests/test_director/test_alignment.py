import glob
from rook.director.alignment import SubsetAlignmentChecker

test_path = "tests/mini-esgf-data/test_data/badc/cmip5/data/cmip5/output1/MOHC/HadGEM2-ES/historical/mon/atmos/Amon" \
            "/r1i1p1/latest/tas/*.nc"
test_paths = glob.glob(test_path)

# inputs = config_args = {
#             'output_dir': self.workdir,
#             'apply_fixes': 
#             'pre_checked': request.inputs['pre_checked'][0].data,
#             'original_files': request.inputs['original_files'][0].data
#             # 'chunk_rules': dconfig.chunk_rules,
#             # 'filenamer': dconfig.filenamer,
#         }
# 
#         subset_args = {
#             'collection': collection,
#         }
#         if 'time' in request.inputs:
#             subset_args['time'] = request.inputs['time'][0].data
#         if 'level' in request.inputs:
#             subset_args['level'] = request.inputs['level'][0].data
#         if 'area' in request.inputs:
#             subset_args['area'] = request.inputs['area'][0].data


def test_no_subset():
    inputs = {}
    sac = SubsetAlignmentChecker(test_paths, inputs)
    assert sac.is_aligned is True
    assert sac.aligned_files == test_paths

    print(test_paths)


# def test_area_subset():
#     inputs = {}
#     sac = SubsetAlignmentChecker(test_paths, inputs)
#     assert sac.is_aligned is True
#     assert sac.aligned_files == test_paths
#
#
def test_time_subset_no_match():
    inputs = {"time": "1886-01-01/1930-11-1"}
    sac = SubsetAlignmentChecker(test_paths, inputs)
    assert sac.is_aligned is True
    assert sac.aligned_files == []
    
    
def test_time_subset_one_match():
    inputs = {"time": "1886-01-01/1984-11-1"}
    sac = SubsetAlignmentChecker(test_paths, inputs)
    assert sac.is_aligned is False
    assert sac.aligned_files == []


def test_time_subset_match():
    inputs = {"time": "1859-12-01/2005-11-1"}
    sac = SubsetAlignmentChecker(test_paths, inputs)
    assert sac.is_aligned is True
    assert sac.aligned_files == test_paths
