# TODO: patch daops for c3s-cmip6-decdal prefix
from daops.utils.base_lookup import Lookup
from roocs_utils.exceptions import InvalidProject
from roocs_utils.project_utils import derive_ds_id

from .director import Director, wrap_director


def _patched_convert_to_ds_id(self):
    """Converts the input dataset to a drs id form to use with the elasticsearch index."""
    try:
        ds_id = derive_ds_id(self.dset)
        # TODO: change prefix in fixer database for c3s-cmip6-decadal
        if ds_id.startswith("c3s-cmip6-decadal"):
            ds_id = "c3s-cmip6." + ds_id.split(".", 1)[1]
        return ds_id
    except InvalidProject:
        raise Exception(
            f"The format of {self.dset} is not known and it could not be converted to a ds id."
        )


Lookup.convert_to_ds_id = _patched_convert_to_ds_id
