import numpy as np
import collections

from roocs_utils.parameter import collection_parameter

from roocs_utils.project_utils import derive_ds_id

from daops.ops.base import Operation
from daops.utils import normalise

from clisops.ops.average import average_over_dims

class WeightedAverage(Operation):
    def _resolve_params(self, collection, **params):
        """
        Resolve the input parameters to `self.params` and parameterise
        collection parameter and set to `self.collection`.
        """
        collection = collection_parameter.CollectionParameter(collection)

        self.collection = collection
        self.params = {
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
            # fix time
            ds['time'] = ds['time'].astype('int64')
            ds['time_bnds'] = ds['time_bnds'].astype('int64')
            # calculate weights
            weights = np.cos(np.deg2rad(ds.lat))
            weights.name = "weights"
            weights.fillna(0)
            # apply weights
            ds_weighted = ds.weighted(weights)
            # add to list
            datasets.append(ds_weighted)

        # average
        outputs = average_over_dims(
            datasets,
            dims=["latitude", "longitude"],
            output_type="nc",
        )
        # result
        rs.add("output", outputs)

        return rs


def run_weighted_average(args):
    result = weighted_average(**args)
    return result.file_uris


def weighted_average(
    collection,
    ignore_undetected_dims=False,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
    apply_fixes=False,
    apply_average=False,
):
    result_set = WeightedAverage(
        collection=collection,
        ignore_undetected_dims=ignore_undetected_dims,
        output_dir=output_dir,
        output_type=output_type,
        split_method=split_method,
        file_namer=file_namer,
        apply_fixes=apply_fixes,
        apply_average=apply_average)._calculate()
    return result_set