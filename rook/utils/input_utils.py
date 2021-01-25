import os

from pywps.app.exceptions import ProcessError
from roocs_utils.project_utils import get_project_name
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
    "Remove common arguments not required in processing calls."
    to_remove = ("pre_checked", "original_files")

    for key in to_remove:
        if key in inputs:
            del inputs[key]


def resolve_collection_if_files(coll):
    # If multiple inputs are files with a common directory name, then
    # return that as a single output

    if len(coll) > 1:
        # Interpret as a sequence of files
        first_dir = os.path.dirname(coll[0])
        files = [fpath.split("/")[-1] for fpath in coll]
        file_glob = ",".join(files)

        # If all are valid file paths and they are all in one directory then return it
        try:
            if all([os.path.isfile(item) for item in coll]):
                if os.path.dirname(os.path.commonprefix(coll)) == first_dir:
                    return f"{first_dir}/{{{file_glob}}}"
        except AssertionError:
            raise Exception(
                "File inputs are not from the same directory so cannot be resolved."
            )

    # if only file then just return that
    return coll[0]


def mapped_urls(coll):
    """ If URLs map them to local file paths """
    project = get_project_name(coll[0])
    download_dir = CONFIG.get(f"project:{project}", {}).get("data_node_root")
    base_dir = CONFIG.get(f"project:{project}", {}).get("base_dir")
    file_paths = [
        os.path.join(base_dir, url.partition(download_dir)[2]) for url in coll
    ]

    return file_paths


def resolve_input(coll):
    # if all URLs
    if all(["https" in item for item in coll]):
        coll = mapped_urls(coll)

    # if not they are files
    # check all exist on file system
    if not all(os.path.isfile(file) for file in coll):
        raise Exception("Files could not be found")

    return resolve_collection_if_files(coll)
