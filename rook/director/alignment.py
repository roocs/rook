import os

import dateutil.parser as parser
from roocs_utils.parameter import time_parameter


class SubsetAlignmentChecker:

    def __init__(self, input_files, inputs):
        self.input_files = sorted(input_files)
        self.is_aligned = False
        self.aligned_files = []

        self._deduce_alignment(inputs)  # needs inputs - where are they coming from

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
        # Use file name to get start and end (instead of reading files)
        start, end = os.path.basename(fpath).split(".")[-2].split("_")[-1].split("-")

        # parser should parse YYYYMM and YYYYMMDDhhmm but doesn't
        start, end = [
            each[:6] + "01" + each[6:] if len(each) == 6 else each
            for each in (start, end)
        ]
        start, end = [
            each[:8] + "T" + each[8:] if len(each) > 8 else each
            for each in (start, end)
        ]
        start, end = (
            parser.isoparse(start).isoformat(),
            parser.isoparse(end).isoformat(),
        )

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

            if fstart >= start or fend <= end:
                self.aligned_files.append(fpath)

        # If there were not 
        if matches != 2:
            self.aligned_files.clear()
            return

        else:
            self.is_aligned = True
            return
