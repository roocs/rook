import os
from pywps.app.exceptions import ProcessError


def parse_wps_input(inputs, key, as_sequence=False, must_exist=False, default=None):

    if not inputs.get(key):
        if must_exist:
            raise ProcessError(f'Required input "{key}" must be provided.')
        else:
            return default
    else:
        value = inputs[key]

    if as_sequence:
        return [dset.data for dset in value]

    else:
        return value[0].data


def clean_inputs(inputs):
    "Remove common arguments not required in processing calls."
    to_remove = ('pre_checked', 'original_files')

    for key in to_remove:
        if key in inputs:
            del inputs[key]


def resolve_collection_if_files(coll):
    # If multiple inputs are files with a common directory name, then
    # return that as a single output

    if len(coll) > 1:
        # Interpret as a sequence of files
        first_dir = os.path.dirname(coll[0])

        # If all are valid file paths and they are all in one directory then return it
        if all([os.path.isfile(item) for item in coll]):
            if os.path.dirname(os.path.commonprefix(coll)) == first_dir:
                return first_dir

    return coll[0]
