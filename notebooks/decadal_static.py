import xarray as xr
import pandas as pd
from pathlib import Path
from memory_profiler import profile


@profile
def get_decdal_static(basedir, time=None):
    data_dir = Path(basedir)
    paths = list(data_dir.glob("**/*.nc"))
    # use a context manager, to ensure the file gets closed after use
    with xr.open_dataset(paths[0]) as ds:
        # select time
        if time is not None:
            ds = ds.isel(time=time)
        # write output
        ds.to_netcdf("out/static.nc")
