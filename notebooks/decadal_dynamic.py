import xarray as xr
import pandas as pd
from pathlib import Path
from memory_profiler import profile


@profile
def get_decdal_dynamic(basedir, time=None):
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
    paths = sorted(data_dir.glob("**/*.nc"))
    datasets = [process_one_path(p) for p in paths]
    # dim
    dim_values = [ds.realization_index for ds in datasets]
    dim = pd.Index(dim_values, name="realization")
    # concat
    # ds_combine = xr.concat(datasets, dim=dim)
    ds_combine = xr.combine_nested(datasets, concat_dim=dim.name)
    # average
    ds_avg = ds_combine.mean(dim=dim.name, skipna=True, keep_attrs=True)
    # write output
    ds_avg.to_netcdf("out/dynamic.nc")
    return ds_avg
