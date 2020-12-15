from roocs_utils.parameter import time_parameter
import dateutil.parser as parser
import os


class SubsetAlignmentChecker:
    def __init__(self, input_files, inputs):
        self.input_files = input_files
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
        # ...loop through the files to see if the `start` happens to match the start
        # of a file and the `end` happens to match the end of a file
        exact_matches = 0

        for fpath in self.input_files:

            fstart, fend = self._get_file_times(fpath)

            if fstart == start:
                exact_matches += 1

            if fend == end:
                exact_matches += 1

            if fstart >= start or fend <= end:
                self.aligned_files.append(fpath)

        if exact_matches != 2:
            self.aligned_files.clear()
            return

        else:
            self.is_aligned = True
            return
