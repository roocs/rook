import os

from pywps.app.exceptions import ProcessError
from roocs_utils.project_utils import url_to_file_path
from roocs_utils.exceptions import InvalidProject
from rook import CONFIG

TC_ALL_MONTHS = "month:jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,dec"
TC_ALL_MONTHS_2 = "month:01,02,03,04,05,06,07,08,09,10,11,12"
TC_ALL_DAYS = "day:01,02,03,04,05,06,07,08,09,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31"


def fix_parameters(parameters):
    if "time_components" in parameters:
        parameters["time_components"] = fix_time_components(
            parameters["time_components"]
        )
    return parameters


def fix_time_components(tc):
    # Remove redundant time-component parts to avoid for example issues with 360day calendars.
    if not tc:
        return None

    tc_parts = tc.split("|")
    new_tc_parts = []
    for tc_part in tc_parts:
        if tc_part == TC_ALL_MONTHS:
            continue
        if tc_part == TC_ALL_MONTHS_2:
            continue
        if tc_part == TC_ALL_DAYS:
            continue
        new_tc_parts.append(tc_part)
    new_tc = "|".join(new_tc_parts)
    return new_tc


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
