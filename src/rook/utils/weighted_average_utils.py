from collections.abc import Sequence
from pathlib import Path
from typing import Optional, Union

import numpy as np
import xarray as xr


from clisops.parameter.dimension_parameter import DimensionParameter

from daops.ops.average import Average as DaopsAverage
from clisops.ops.average import Average as ClisopsAverage
from clisops.utils.file_namers import get_file_namer


def calc_weighted_mean(ds):
    # fix cftime calendar
    ds["time"] = ds.indexes["time"].to_numpy()
    ds = ds.drop_vars(["time_bnds"])
    # weights
    weights = np.cos(np.deg2rad(ds.lat))
    weights.name = "weights"
    weights.fillna(0)
    # apply weights
    ds_weighted = ds.weighted(weights)
    # apply mean
    ds_weighted_mean = ds_weighted.mean(["lat", "lon"], keep_attrs=True)
    return ds_weighted_mean


class WeightedAverage_(ClisopsAverage):  # noqa: N801
    def _get_file_namer(self):
        extra = "_w-avg"

        namer = get_file_namer(self._file_namer)(extra=extra)

        return namer

    def _calculate(self):
        avg_ds = calc_weighted_mean(self.ds)

        return avg_ds


def _weighted_average(
    ds: Union[xr.Dataset, str],
    dims: Optional[Union[Sequence[str], DimensionParameter]] = None,
    ignore_undetected_dims: bool = False,
    output_dir: Optional[Union[str, Path]] = None,
    output_type: str = "netcdf",
    split_method: str = "time:auto",
    file_namer: str = "standard",
) -> list[Union[xr.Dataset, str]]:
    op = WeightedAverage_(**locals())
    return op.process()


class WeightedAverage(DaopsAverage):
    def get_operation_callable(self):
        return _weighted_average


def weighted_average(
    collection,
    dims=None,
    ignore_undetected_dims=False,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
    apply_fixes=False,
):
    result_set = WeightedAverage(**locals()).calculate()
    return result_set


def run_weighted_average(args):
    result = weighted_average(**args)
    return result.file_uris
