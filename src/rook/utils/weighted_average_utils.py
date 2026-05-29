from collections.abc import Sequence
from pathlib import Path

import numpy as np
import xarray as xr


from clisops.parameter.dimension_parameter import DimensionParameter

from clisops.ops.average import Average as ClisopsAverage
from clisops.utils.file_namers import get_file_namer
from rook.utils.ops_compat import run_daops_custom_average


def calc_weighted_mean(ds):
    # fix cftime calendar
    ds["time"] = ds.indexes["time"].to_numpy()
    ds = ds.drop_vars(["time_bnds"], errors="ignore")
    # Generate weights with both lat & lon dimensions
    weights = np.cos(np.deg2rad(ds.lat))
    weights = weights / weights.sum()  # Normalize
    weights = weights.broadcast_like(ds)  # Ensure shape matches ds
    weights.name = "weights"
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
    ds: xr.Dataset | str,
    dims: Sequence[str] | DimensionParameter | None = None,
    ignore_undetected_dims: bool = False,
    output_dir: str | Path | None = None,
    output_type: str = "netcdf",
    split_method: str = "time:auto",
    file_namer: str = "standard",
) -> list[xr.Dataset | str]:
    op = WeightedAverage_(**locals())
    return op.process()


def run_weighted_average(args):
    return run_daops_custom_average(args, _weighted_average)
