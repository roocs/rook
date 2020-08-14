import os
import subprocess
from glob import glob


# generate condensed versions of data to use as test data

Amon_file_path = "/badc/cmip5/data/cmip5/output1/MOHC/HadGEM2-ES/rcp85/mon/atmos/Amon/r1i1p1/latest/tas"
zostoga_file_path = "/badc/cmip5/data/cmip5/output1/IPSL/IPSL-CM5A-MR/rcp45/mon/ocean/Omon/r1i1p1/latest/zostoga"
cordex_IPSL_file_path = "/group_workspaces/jasmin2/cp4cds1/data/c3s-cordex/output/EUR-11/IPSL/MOHC-HadGEM2-ES/rcp85/r1i1p1/IPSL-WRF381P/v1/day/psl/v20190212"
no_time_name = "/group_workspaces/jasmin2/cp4cds1/vol1/data/c3s-cmip5/output1/ICHEC/EC-EARTH/historical/day/atmos/day/r1i1p1/tas/v20131231"
CMIP6_siconc = "/badc/cmip6/data/CMIP6/CMIP/NCAR/CESM2/historical/r1i1p1f1/SImon/siconc/gn/latest"
cmip5_tas = "/badc/cmip5/data/cmip5/output1/NCAR/CCSM4/historical/mon/atmos/Amon/r1i1p1/latest/tas"

fpath = cmip5_tas
filelist = glob(f'{fpath}/*.nc')
output_path = f"test_data{fpath}"

for file in filelist:
    path = f"{file}"
    f = file.split('/')[-1]
    var_id = f.split("_")[0]
    output_file = f"test_data{file}"
    if not os.path.exists(output_file):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    lat_selector = "-d lat,,,100"
    lon_selector = "-d lon,,,100"

    extra = ""

    if "zostoga" in file:
        lon_selector = ""
        lat_selector = ""
        if "inm" in file:
            extra = "-d lev,,,8"

    if "cordex" in file:
        lon_selector = "-d rlat,,,100"
        lat_selector = "-d rlon,,,100"
        extra = ""

    if "siconc" in file:
        lon_selector = ""
        lat_selector = ""
        extra = "-d ni,,,100 -d nj,,,100"

    cmd = f"ncks {extra} {lat_selector} {lon_selector} --variable {var_id} {path} {output_file}"
    print("running", cmd)
    subprocess.call(cmd, shell=True)
