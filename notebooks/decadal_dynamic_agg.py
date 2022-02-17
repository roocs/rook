import xarray as xr
import pandas as pd
from pathlib import Path
from memory_profiler import profile


@profile
def get_decdal_dynamic_agg(basedir, time=None):
    data_dir = Path(basedir)
    paths = sorted(data_dir.glob("**/*.nc"))

    # aggregation
    with xr.open_mfdataset(paths, concat_dim="realization", combine="nested") as ds:
        # average
        ds_avg = ds.mean(dim="realization", skipna=True, keep_attrs=True)
        # select time
        if time is not None:
            ds_avg.isel(time=time)
        # write output
        ds_avg.to_netcdf("out/dynamic_agg.nc")
