import xarray as xr
import pandas as pd
from pathlib import Path
from memory_profiler import profile


@profile
def get_decdal_static(basedir, time=None):
    def process_one_path(path):
        # use a context manager, to ensure the file gets closed after use
        with xr.open_dataset(path) as ds:
            # select time
            if time is not None:
                ds = ds.isel(time=time)
            # load all data from the transformed dataset, to ensure we can
            # use it after closing each original file
            ds.load()
            return ds

    data_dir = Path(basedir)
    paths = list(data_dir.glob("**/*.nc"))
    ds = process_one_path(paths[0])
    # write output
    ds.to_netcdf("out/static.nc")
    return ds
