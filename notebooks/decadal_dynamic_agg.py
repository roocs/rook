from pathlib import Path

import pandas as pd
import xarray as xr
from memory_profiler import profile


@profile
def get_decdal_dynamic_agg(basedir, time=None):
    data_dir = Path(basedir)
    paths = sorted(data_dir.glob("**/*.nc"))

    # aggregation
    with xr.open_mfdataset(
        paths,
        concat_dim="realization",
        combine="nested",
        chunks={"realization": 10, "time": 10},
        # parallel=True,
        # preprocess=lambda ds: ds.isel(time=0)
    ) as ds:
        # average
        ds_avg = ds.mean(dim="realization", skipna=True, keep_attrs=True)
        # select time
        if time is not None:
            ds_avg.isel(time=time)
        # write output
        ds_avg.to_netcdf("out/dynamic_agg.nc")


if __name__ == "__main__":
    get_decdal_dynamic_agg("/Users/pingu/data/cmip6-decadal/orig/day")
