import os
import xarray as xr

import dateutil.parser as parser
from roocs_utils.parameter import time_parameter
from roocs_utils.utils.time_utils import to_isoformat
from roocs_utils.project_utils import url_to_file_path


class SubsetAlignmentChecker:
    def __init__(self, input_files, inputs):
        self.input_files = sorted(input_files)
        self.is_aligned = False
        self.aligned_files = []

        self._deduce_alignment(inputs)

    def _deduce_alignment(self, inputs):
        # At present, we reject alignment if any "area" or "level" subset is requested
        if inputs.get("area", None) or inputs.get("level", None):
            return

        time = inputs.get("time", None)

        # add in a catch for if time tuple is None
        # this means is_aligned = True and all files are needed
        if time is None:
            self.is_aligned = True
            self.aligned_files = self.input_files
            return

        else:
            start, end = time_parameter.TimeParameter(time).tuple
            self._check_time_alignment(start, end)

    def _get_file_times(self, fpath):
        # get start and end times from the time dimension in the file

        # convert url to file path if needed
        if fpath.startswith("https"):
            fpath = url_to_file_path(fpath)

        ds = xr.open_dataset(fpath, use_cftime=True)
        start = to_isoformat(ds.time.values[0])
        end = to_isoformat(ds.time.values[-1])
        ds.close()
        return start, end

    def _check_time_alignment(self, start, end):
        """
        Loops through all data files to check if the `start` and `end` can be aligned
        with the exact start or end time in the file(s).

        If both the `start` and the `end` are aligned then the following properties
        are set:
         - self.aligned_files = [list of matching files in range]
         - self.is_aligned = True

        If the `start` is before the start time of the first file and/or
        the `end` is after the end time of the last file then that is considered
        a valid match to the required time range.
        """
        # Set matches as a counter to see if we get valid time alignment.
        # Must result in matches==2 in order to be valid.
        matches = 0

        # First of all truncate requested range to actual range if it extends
        # beyond the actual range in the files

        start_in_files, _ = self._get_file_times(self.input_files[0])
        _, end_in_files = self._get_file_times(self.input_files[-1])

        if start < start_in_files:
            start = start_in_files

        if end > end_in_files:
            end = end_in_files

        # Now go through files to check alignment
        for fpath in self.input_files:

            fstart, fend = self._get_file_times(fpath)

            # Break out if start of file is beyond end of requested range
            if fstart > end:
                break

            if fstart == start:
                matches += 1

            if fend == end:
                matches += 1

            if fstart >= start or end <= fend:
                self.aligned_files.append(fpath)

        if matches != 2:
            self.aligned_files.clear()
            return

        else:
            self.is_aligned = True
            return
