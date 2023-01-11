from clisops.ops.average import average_over_dims as clisops_average_over_dims
from roocs_utils.parameter import collection_parameter

# from roocs_utils.parameter import dimension_parameter

from daops.ops.base import Operation
from daops.processor import process
from daops.utils import normalise


from collections.abc import Sequence

from roocs_utils.exceptions import InvalidParameterValue
from roocs_utils.parameter.base_parameter import _BaseParameter

# from roocs_utils.xarray_utils.xarray_utils import known_coord_types
from roocs_utils.parameter.param_utils import dimensions, parse_sequence


class DimensionParameter(_BaseParameter):
    """
    Class for dimensions parameter used in averaging operation.

    | Area can be input as:
    | A string of comma separated values: "time,latitude,longitude"
    | A sequence of strings: ("time", "longitude")

    Dimensions can be None or any number of options from time, latitude, longitude and level provided these
    exist in the dataset being operated on.

    Validates the dims input and parses the values into a sequence of strings.

    """

    allowed_input_types = [Sequence, str, dimensions, type(None)]

    def _parse(self):
        classname = self.__class__.__name__

        if self.input in (None, ""):
            return None
        elif isinstance(self.input, dimensions):
            value = self.input.value
        else:
            value = parse_sequence(self.input, caller=classname)

        for item in value:
            if not isinstance(item, str):
                raise InvalidParameterValue("Each dimension must be a string.")

            # if item not in known_coord_types:
            #     raise InvalidParameterValue(
            #         f"Dimensions for averaging must be one of {known_coord_types}"
            #     )

        return tuple(value)

    def asdict(self):
        """Returns a dictionary of the dimensions"""
        if self.value is not None:
            return {"dims": self.value}

    def __str__(self):
        return f"Dimensions to average over:" f"\n {self.value}"


class Concat(Operation):
    def _resolve_params(self, collection, **params):
        """
        Resolve the input parameters to `self.params` and parameterise
        collection parameter and set to `self.collection`.
        """
        dims = DimensionParameter(params.get("dims"))
        collection = collection_parameter.CollectionParameter(collection)

        self.collection = collection
        self.params = {
            "dims": dims,
            "ignore_undetected_dims": params.get("ignore_undetected_dims"),
        }

    def get_operation_callable(self):
        return clisops_average_over_dims

    def _calculate(self):
        config = {
            "output_type": self._output_type,
            "output_dir": self._output_dir,
            "split_method": self._split_method,
            "file_namer": self._file_namer,
        }

        self.params.update(config)

        # Normalise (i.e. "fix") data inputs based on "character"
        norm_collection = normalise.normalise(self.collection, self._apply_fixes)

        rs = normalise.ResultSet(vars())

        # change name of data ref here
        for dset, norm_collection in norm_collection.items():
            # Process each input dataset (either in series or
            # parallel)
            rs.add(
                dset,
                process(self.get_operation_callable(), norm_collection, **self.params),
            )

        return rs


def _concat(
    collection,
    dims=None,
    ignore_undetected_dims=False,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
    apply_fixes=True,
):
    result_set = Concat(**locals())._calculate()
    return result_set


def run_concat(args):
    result = concat(**args)
    return result.file_uris


def concat(
    collection,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
    apply_fixes=True,
):
    # dummy concat operator
    # from daops.ops.average import average_over_dims

    args = dict(
        collection=collection,
        dims=["realization"],
        output_dir=output_dir,
        output_type=output_type,
        split_method=split_method,
        file_namer=file_namer,
        apply_fixes=apply_fixes,
    )
    return _concat(**args)
