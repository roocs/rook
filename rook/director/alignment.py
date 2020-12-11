from roocs_utils.parameter import time_parameter


class SubsetAlignmentChecker:

    def __init__(self, input_files):
        self.input_files = input_files
        self.is_aligned = False
        self.aligned_files = []

        self._deduce_alignment()

    def _deduce_alignment(self, inputs):
        # At present, we reject alignment if any "area" or "level" subset is requested
        if inputs.get('area', None) or inputs.get('level', None):
            return

        start, end = time_parameter.TimeParameter(time).tuple
        self._check_time_alignment(start, end)

    def _get_file_times(self, fpath):
        # Use file name to get start and end (instead of reading files)
        time_strings = os.path.basename(fpath).split('.')[-2].split('_').[-1].split('-')
        start, end = TODO: convert datetime to isotime strings (might be "YYYY", "YYYYMM", "YYYYMMDD", "YYYYMMDDhh", "YYYYMMDDhhmm")
        return start, end

    def _check_time_alignment(self, start, end):
        ...loop through the files to see if the `start` happens to match the start
        of a file and the `end` happens to match the end of a file
        If NOT: return 
        If YES:
           self.is_aligned = True
           self.aligned_files = [those files that are in the aligned set]
           return