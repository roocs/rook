import os

from clisops.ops.subset import subset as clisops_subset
from roocs_utils.parameter import parameterise

from daops.processor import process
from daops.utils import consolidate
from daops.utils import normalise

import logging
LOGGER = logging.getLogger()


def subset(
    collection,
    time=None,
    area=None,
    level=None,
    output_dir=None,
    output_type="netcdf",
    split_method="time:auto",
    file_namer="standard",
):
    """
    Tweak daops.ops.subset
    """
    parameters = parameterise(collection=collection, time=time, area=area, level=level)

    # Consolidate data inputs so they can be passed to Xarray
    collection = parameters.get("collection")
    LOGGER.debug(f"collection={collection.tuple}")
    if collection.tuple and os.path.isfile(collection.tuple[0]):
        collection = dict(files=collection)
    else:
        collection = consolidate.consolidate(
            collection, time=parameters.get("time")
        )
    LOGGER.debug(f"consolidated collection={collection}")
    # Normalise (i.e. "fix") data inputs based on "character"
    norm_collection = normalise.normalise(collection)
    LOGGER.debug(f"norm collection={norm_collection}")

    rs = normalise.ResultSet(vars())
    # change name of data ref here
    for dset, norm_collection in norm_collection.items():

        # Process each input dataset (either in series or
        # parallel)
        rs.add(
            dset,
            process(
                clisops_subset,
                norm_collection,
                **{
                    "time": parameters.get("time"),
                    "area": parameters.get("area"),
                    "level": parameters.get("level"),
                    "output_type": output_type,
                    "output_dir": output_dir,
                    "split_method": split_method,
                    "file_namer": file_namer,
                },
            ),
        )

    return rs
