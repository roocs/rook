import os

from pywps.app.exceptions import ProcessError
from roocs_utils.project_utils import url_to_file_path
from roocs_utils.exceptions import InvalidProject
from rook import CONFIG


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
    """Remove common arguments not required in processing calls."""
    to_remove = ("pre_checked", "original_files")

    for key in to_remove:
        if key in inputs:
            del inputs[key]


def resolve_to_file_paths(coll):
    # if a mixed collection
    if not all([item.startswith("http") or item.startswith("/") for item in coll]):
        raise Exception("Collections containing file paths and URLs are not accepted.")

    # if all URLs
    if all([item.startswith("http") for item in coll]):
        try:
            file_paths = [url_to_file_path(item) for item in coll]
        except InvalidProject:
            raise Exception("The URLs could not be mapped to file paths")

    # otherwise they are all file paths
    else:
        file_paths = coll

    return file_paths
