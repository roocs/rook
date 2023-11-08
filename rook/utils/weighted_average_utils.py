import numpy as np

import xarray as xr

import collections

from roocs_utils.parameter import collection_parameter
from roocs_utils.parameter import dimension_parameter

from roocs_utils.project_utils import derive_ds_id

from daops.ops.base import Operation
from daops.utils import normalise

from clisops.ops import subset

# from clisops.ops.average import average_over_dims as average


def apply_weighted_mean(ds):
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
    ds_weighted_mean = ds_weighted.mean(["lat", "lon"])
    return ds_weighted_mean


class WeightedAverage(Operation):
    def _resolve_params(self, collection, **params):
        """
        Resolve the input parameters to `self.params` and parameterise
        collection parameter and set to `self.collection`.
        """
        dims = dimension_parameter.DimensionParameter(["latitude", "longitude"])
        collection = collection_parameter.CollectionParameter(collection)

        self.collection = collection
        self.params = {
            "dims": dims,
            "ignore_undetected_dims": params.get("ignore_undetected_dims"),
        }

    def _calculate(self):
        config = {
            "output_type": self._output_type,
            "output_dir": self._output_dir,
            "split_method": self._split_method,
            "file_namer": self._file_namer,
        }

        self.params.update(config)

        new_collection = collections.OrderedDict()

        for dset in self.collection:
            ds_id = derive_ds_id(dset)
            new_collection[ds_id] = dset.file_paths

        # Normalise (i.e. "fix") data inputs based on "character"
        norm_collection = normalise.normalise(
            new_collection, False  # self._apply_fixes
        )

        rs = normalise.ResultSet(vars())

        # apply weights
        datasets = []
        for ds_id in norm_collection.keys():
            ds = norm_collection[ds_id]
            ds_mod = apply_weighted_mean(ds)
            datasets.append(ds_mod)

        processed_ds = datasets[0]

        # subset
        outputs = subset(
            processed_ds,
            time=None,
            file_namer="simple",
            output_type="netcdf",
        )
        # result
        rs.add("output", outputs)

        return rs


def run_weighted_average(args):
    result = weighted_average(**args)
    return result.file_uris


def weighted_average(
    collection,
    dims=None,
    ignore_undetected_dims=False,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="simple",
    apply_fixes=False,
):
    result_set = WeightedAverage(**locals())._calculate()
    return result_set
